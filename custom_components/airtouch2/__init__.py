"""The airtouch2 integration."""
from __future__ import annotations

import logging

from airtouch2.at2 import At2Client

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
        device_id = call.data.get("device_id")
        
        if device_id:
            # Find the config entry for this device
            device_registry = dr.async_get(hass)
            device = device_registry.async_get(device_id)
            
            if not device:
                _LOGGER.error("Device not found: %s", device_id)
                return
                
            # Find config entry
            config_entry_id = None
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN:
                    # Find config entry by checking all entries
                    for entry_id, data in hass.data[DOMAIN].items():
                        if entry_id in hass.config_entries.async_entries(DOMAIN):
                            config_entry_id = entry_id
                            break
                    break
                    
            if config_entry_id and config_entry_id in hass.data[DOMAIN]:
                monitor = hass.data[DOMAIN][config_entry_id]["monitor"]
                success = await monitor.force_reconnect()
                if success:
                    _LOGGER.info("Successfully reconnected AirTouch2")
                else:
                    _LOGGER.error("Failed to reconnect AirTouch2")
            else:
                _LOGGER.error("Could not find AirTouch2 integration for device")
        else:
            # Reconnect all AirTouch2 integrations
            for entry_id, data in hass.data[DOMAIN].items():
                if isinstance(data, dict) and "monitor" in data:
                    monitor = data["monitor"]
                    await monitor.force_reconnect()
    
    # Register the reconnect service
    hass.services.async_register(
        DOMAIN,
        "reconnect",
        async_reconnect_service,
        schema=None,  # We'll accept any data
    )