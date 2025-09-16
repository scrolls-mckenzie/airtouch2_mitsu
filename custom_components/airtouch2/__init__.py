"""The airtouch2 integration."""
from __future__ import annotations

import logging

from .airtouch2.at2 import At2Client

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .connection_monitor import AirTouch2ConnectionMonitor

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.FAN]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up airtouch2 from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    client = At2Client(entry.data[CONF_HOST])
    if not await client.connect():
        raise ConfigEntryNotReady(
            f"Airtouch2 client failed to connect to {entry.data[CONF_HOST]}")
    client.run()
    await client.wait_for_ac()
    if not client.aircons_by_id:
        raise ConfigEntryNotReady("No AC units were found")
    
    # Create connection monitor
    def on_reconnect():
        """Handle reconnection - update all entities."""
        _LOGGER.info("AirTouch2 reconnected, updating entities")
        hass.async_create_task(
            hass.config_entries.async_reload(entry.entry_id)
        )
    
    monitor = AirTouch2ConnectionMonitor(
        hass, client, entry.data[CONF_HOST], on_reconnect
    )
    
    # Store both client and monitor
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "monitor": monitor,
        "host": entry.data[CONF_HOST]
    }
    
    # Start monitoring
    monitor.start_monitoring()
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_register_services(hass)

    # Reload entry when its updated.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = hass.data[DOMAIN][entry.entry_id]
        client: At2Client = data["client"]
        monitor: AirTouch2ConnectionMonitor = data["monitor"]
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Stop client
        await client.stop()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register AirTouch2 services."""
    
    async def async_reconnect_service(call: ServiceCall) -> None:
        """Service to force reconnect AirTouch2."""
        _LOGGER.info("AirTouch2 reconnect service called")
        
        # Reconnect all AirTouch2 integrations
        reconnected_count = 0
        for entry_id, data in hass.data[DOMAIN].items():
            if isinstance(data, dict) and "monitor" in data:
                monitor = data["monitor"]
                try:
                    success = await monitor.force_reconnect()
                    if success:
                        reconnected_count += 1
                        _LOGGER.info("Successfully reconnected AirTouch2 integration %s", entry_id)
                    else:
                        _LOGGER.error("Failed to reconnect AirTouch2 integration %s", entry_id)
                except Exception as err:
                    _LOGGER.error("Error reconnecting AirTouch2 integration %s: %s", entry_id, err)
        
        if reconnected_count > 0:
            _LOGGER.info("Reconnected %d AirTouch2 integration(s)", reconnected_count)
        else:
            _LOGGER.warning("No AirTouch2 integrations were reconnected")
    
    # Register the reconnect service (only register once)
    if not hass.services.has_service(DOMAIN, "reconnect"):
        hass.services.async_register(
            DOMAIN,
            "reconnect",
            async_reconnect_service,
        )