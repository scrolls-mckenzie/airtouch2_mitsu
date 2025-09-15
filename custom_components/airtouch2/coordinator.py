"""DataUpdateCoordinator for AirTouch2."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from airtouch2.at2 import At2Client

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AirTouch2Coordinator(DataUpdateCoordinator):
    """Class to manage fetching AirTouch2 data."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        """Initialize."""
        self.host = host
        self.client = At2Client(host)
        self._connected = False
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library."""
        if not self._connected:
            try:
                if not await self.client.connect():
                    raise UpdateFailed("Failed to connect to AirTouch2")
                
                self.client.run()
                await asyncio.wait_for(self.client.wait_for_ac(), timeout=10.0)
                self._connected = True
                _LOGGER.info("Connected to AirTouch2 at %s", self.host)
                
            except asyncio.TimeoutError as err:
                raise UpdateFailed("Timeout connecting to AirTouch2") from err
            except Exception as err:
                raise UpdateFailed(f"Error connecting to AirTouch2: {err}") from err
        
        # Return the current system info
        return {
            "system_info": self.client.system_info,
            "aircons": dict(self.client.aircons_by_id),
            "groups": dict(self.client.groups_by_id),
        }
    
    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self._connected:
            await self.client.stop()
            self._connected = False
            _LOGGER.info("Disconnected from AirTouch2 at %s", self.host)