"""Connection monitoring and auto-reconnection for AirTouch2."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from airtouch2.at2 import At2Client
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

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
        self._last_update = datetime.now()
        self._monitoring = False
        self._reconnecting = False
        self._monitor_task = None
        self._check_interval = timedelta(seconds=30)  # Check every 30 seconds
        self._timeout_threshold = timedelta(minutes=2)  # Consider dead after 2 minutes
        
    def update_last_seen(self) -> None:
        """Update the last seen timestamp."""
        self._last_update = datetime.now()
        
    def start_monitoring(self) -> None:
        """Start connection monitoring."""
        if self._monitoring:
            return
            
        _LOGGER.debug("Starting AirTouch2 connection monitoring")
        self._monitoring = True
        
        # Schedule periodic checks
        self._monitor_task = async_track_time_interval(
            self.hass,
            self._check_connection,
            self._check_interval
        )
        
    def stop_monitoring(self) -> None:
        """Stop connection monitoring."""
        if not self._monitoring:
            return
            
        _LOGGER.debug("Stopping AirTouch2 connection monitoring")
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task()
            self._monitor_task = None
            
    async def _check_connection(self, now: datetime) -> None:
        """Check if connection is still alive."""
        if self._reconnecting:
            return
            
        time_since_update = now - self._last_update
        
        if time_since_update > self._timeout_threshold:
            _LOGGER.warning(
                "AirTouch2 connection appears dead (no updates for %s), attempting reconnection",
                time_since_update
            )
            await self._reconnect()
            
    async def _reconnect(self) -> None:
        """Attempt to reconnect to AirTouch2."""
        if self._reconnecting:
            return
            
        self._reconnecting = True
        
        try:
            _LOGGER.info("Attempting to reconnect to AirTouch2 at %s", self.host)
            
            # Stop the current client
            await self.client.stop()
            
            # Wait a bit before reconnecting
            await asyncio.sleep(2)
            
            # Try to reconnect
            if await self.client.connect():
                _LOGGER.info("Successfully reconnected to AirTouch2")
                self.client.run()
                await self.client.wait_for_ac(timeout=10)
                self.update_last_seen()
                
                # Notify entities about reconnection
                if self.reconnect_callback:
                    self.reconnect_callback()
                
                # Force update all entities
                await self._force_entity_updates()
                    
            else:
                _LOGGER.error("Failed to reconnect to AirTouch2, will retry later")
                
        except Exception as err:
            _LOGGER.error("Error during AirTouch2 reconnection: %s", err)
            
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
                for callback in ac._callbacks:
                    try:
                        callback()
                    except Exception as err:
                        _LOGGER.debug("Error calling AC callback: %s", err)
            
            for group in self.client.groups_by_id.values():
                for callback in group._callbacks:
                    try:
                        callback()
                    except Exception as err:
                        _LOGGER.debug("Error calling group callback: %s", err)
                        
        except Exception as err:
            _LOGGER.debug("Error forcing entity updates: %s", err)