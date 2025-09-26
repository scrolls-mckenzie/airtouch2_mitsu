"""Connection monitoring and auto-reconnection for AirTouch2."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from .airtouch2.at2 import At2Client
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class AirTouch2ConnectionMonitor:
    """Monitor AirTouch2 connection and handle reconnection."""
    
    def __init__(
        self, 
        hass: HomeAssistant, 
        client: At2Client, 
        host: str,
        reconnect_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """Initialize the connection monitor."""
        self.hass = hass
        self.client = client
        self.host = host
        self.reconnect_callback = reconnect_callback
        self._last_update = dt_util.utcnow()
        self._monitoring = False
        self._reconnecting = False
        self._monitor_task = None
        self._check_interval = timedelta(seconds=30)  # Check every 30 seconds
        self._timeout_threshold = timedelta(minutes=2)  # Consider dead after 2 minutes
        self._original_handle_message = None
        self._status_request_count = 0
        
    def update_last_seen(self) -> None:
        """Update the last seen timestamp."""
        self._last_update = dt_util.utcnow()
        
    def start_monitoring(self) -> None:
        """Start connection monitoring."""
        if self._monitoring:
            return
            
        _LOGGER.debug("Starting AirTouch2 connection monitoring")
        self._monitoring = True
        
        # Hook into client's message handling to track updates
        self._hook_client_updates()
        
        # Schedule periodic checks
        try:
            self._monitor_task = async_track_time_interval(
                self.hass,
                self._check_connection,
                self._check_interval
            )
        except Exception as err:
            _LOGGER.error("Failed to start connection monitoring: %s", err)
            self._monitoring = False
        
    def stop_monitoring(self) -> None:
        """Stop connection monitoring."""
        if not self._monitoring:
            return
            
        _LOGGER.debug("Stopping AirTouch2 connection monitoring")
        self._monitoring = False
        
        # Restore original client message handling
        self._unhook_client_updates()
        
        if self._monitor_task:
            self._monitor_task()
            self._monitor_task = None
            
    async def _check_connection(self, now: datetime) -> None:
        """Check if connection is still alive."""
        if self._reconnecting:
            return
        
        try:
            # Ensure both datetimes are timezone-aware for comparison
            current_time = now if now.tzinfo else dt_util.utcnow()
            last_update = self._last_update if self._last_update.tzinfo else dt_util.utcnow()
            
            time_since_update = current_time - last_update
            
            # If we haven't received updates for 1 minute, send a status request
            if time_since_update > timedelta(minutes=1):
                if self._status_request_count < 3:  # Try up to 3 status requests
                    _LOGGER.debug("No updates for %s, requesting status (attempt %d)", 
                                time_since_update, self._status_request_count + 1)
                    try:
                        from .airtouch2.protocol.at2.messages.RequestState import RequestState
                        await self.client.send(RequestState())
                        self._status_request_count += 1
                    except Exception as err:
                        _LOGGER.debug("Failed to send status request: %s", err)
                        self._status_request_count += 1
            else:
                # Reset counter when we get updates
                self._status_request_count = 0
            
            # If still no updates after 3 minutes or 3 failed status requests, attempt reconnection
            if time_since_update > timedelta(minutes=3) or self._status_request_count >= 3:
                _LOGGER.warning(
                    "AirTouch2 connection appears dead (no updates for %s, %d status requests sent), attempting reconnection",
                    time_since_update, self._status_request_count
                )
                await self._reconnect()
        except Exception as err:
            _LOGGER.debug("Error checking connection: %s", err)
            
    async def _reconnect(self) -> None:
        """Attempt to reconnect to AirTouch2."""
        if self._reconnecting:
            return
            
        self._reconnecting = True
        
        try:
            _LOGGER.info("Attempting to reconnect to AirTouch2 at %s", self.host)
            
            # Stop the current client and unhook monitoring
            self._unhook_client_updates()
            await self.client.stop()
            
            # Wait longer before reconnecting to allow network recovery
            await asyncio.sleep(5)
            
            # Try to reconnect with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    _LOGGER.debug(f"Reconnection attempt {attempt + 1}/{max_retries}")
                    
                    if await self.client.connect():
                        _LOGGER.info("Successfully reconnected to AirTouch2")
                        
                        # Re-hook monitoring before starting client
                        self._hook_client_updates()
                        
                        self.client.run()
                        await self.client.wait_for_ac(timeout=15)  # Longer timeout
                        self.update_last_seen()
                        self._status_request_count = 0  # Reset counter after successful reconnection
                        
                        # Notify entities about reconnection
                        if self.reconnect_callback:
                            self.reconnect_callback()
                        
                        # Force update all entities
                        await self._force_entity_updates()
                        return  # Success, exit retry loop
                        
                    else:
                        _LOGGER.warning(f"Reconnection attempt {attempt + 1} failed")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                            
                except Exception as retry_err:
                    _LOGGER.warning(f"Reconnection attempt {attempt + 1} error: %s", retry_err)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
            
            _LOGGER.error("All reconnection attempts failed, will retry later")
                
        except Exception as err:
            _LOGGER.error("Error during AirTouch2 reconnection: %s", err)
            # Add debug info to help identify the issue
            _LOGGER.debug("Reconnection error details: %s", str(err))
            
        finally:
            self._reconnecting = False
            
    async def force_reconnect(self) -> bool:
        """Force a reconnection attempt."""
        _LOGGER.info("Force reconnecting AirTouch2 connection")
        await self._reconnect()
        return not self._reconnecting  # Return True if reconnection succeeded
    
    async def _force_entity_updates(self) -> None:
        """Force all entities to update their state."""
        try:
            # Trigger callbacks for all ACs and groups to update their entities
            for ac in self.client.aircons_by_id.values():
                try:
                    for callback in ac._callbacks:
                        try:
                            callback()
                        except Exception as err:
                            _LOGGER.debug("Error calling AC callback: %s", err)
                except AttributeError:
                    # AC might not have _callbacks attribute
                    pass
            
            for group in self.client.groups_by_id.values():
                try:
                    for callback in group._callbacks:
                        try:
                            callback()
                        except Exception as err:
                            _LOGGER.debug("Error calling group callback: %s", err)
                except AttributeError:
                    # Group might not have _callbacks attribute
                    pass
                        
        except Exception as err:
            _LOGGER.debug("Error forcing entity updates: %s", err)
    
    def _hook_client_updates(self) -> None:
        """Hook into client's message handling to track updates."""
        if hasattr(self.client, '_handle_one_message'):
            self._original_handle_message = self.client._handle_one_message
            
            async def monitored_handle_message():
                """Wrapper that updates last seen timestamp."""
                try:
                    result = await self._original_handle_message()
                    self.update_last_seen()
                    return result
                except Exception as err:
                    _LOGGER.debug("Error in message handling: %s", err)
                    raise
            
            self.client._handle_one_message = monitored_handle_message
    
    def _unhook_client_updates(self) -> None:
        """Restore original client message handling."""
        if self._original_handle_message and hasattr(self.client, '_handle_one_message'):
            self.client._handle_one_message = self._original_handle_message
            self._original_handle_message = None