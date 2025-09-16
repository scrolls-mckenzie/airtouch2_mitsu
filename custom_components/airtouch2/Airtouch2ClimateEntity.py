from airtouch2.at2 import At2Aircon
from airtouch2.protocol.at2.enums import ACMode
from .conversions import (
    AT2_TO_HA_MODE,
    AT2_TO_HA_FAN_SPEED,
    HA_MODE_TO_AT2,
    HA_FAN_SPEED_TO_AT2
)
from .const import DOMAIN

from typing import final
import asyncio
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    UnitOfTemperature,
    ATTR_TEMPERATURE,
    PRECISION_WHOLE
)
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)

@final
class Airtouch2ClimateEntity(ClimateEntity):
    """Representation of an AirTouch 2 AC."""

    #
    # Entity attributes:
    #
    _attr_should_poll: bool = False

    #
    # ClimateEntity attributes:
    #
    _attr_precision: float = PRECISION_WHOLE
    _attr_target_temperature_step: float = 1.0
    _attr_temperature_unit: str = UnitOfTemperature.CELSIUS

    def __init__(
        self, airtouch2_aircon: At2Aircon
    ) -> None:
        """Initialize the climate device."""
        _LOGGER.debug(f"Initializing climate device '{airtouch2_aircon.info.name}'")
        self._ac = airtouch2_aircon

    #
    # Entity overrides:
    #

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"at2_ac_{self._ac.info.number}"

    @property
    def name(self):
        """Return the name of the entity."""
        return f"AC {self._ac.info.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer="Polyaire",
            model="Airtouch 2",
            sw_version=f"AC {self._ac.info.number}",
        )
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if we have recent data from the AC
        return self._ac.info is not None
    
    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return False
    
    async def async_update(self) -> None:
        """Update the entity state."""
        # Force a state write to ensure HA has the latest data
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        # Add callback for when aircon receives new data.
        # Removes callback on remove.
        self.async_on_remove(self._ac.add_callback(self._on_aircon_update))
        
    def _on_aircon_update(self) -> None:
        """Handle aircon update and notify connection monitor."""
        # Update connection monitor that we received data
        try:
            for data in self.hass.data[DOMAIN].values():
                if isinstance(data, dict) and "monitor" in data:
                    data["monitor"].update_last_seen()
                    break
        except Exception:
            pass  # Ignore errors in connection monitoring
        
        # Schedule state update on the event loop
        if self.hass:
            self.hass.async_create_task(self._async_update_ha_state())
    
    async def _async_update_ha_state(self) -> None:
        """Update Home Assistant state asynchronously."""
        self.async_write_ha_state()

    #
    # ClimateEntity overrides:
    #

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        if not self._ac.info.active:
            return HVACMode.OFF

        return AT2_TO_HA_MODE[self._ac.info.mode]

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return list(AT2_TO_HA_MODE.values()) + [HVACMode.OFF]

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._ac.info.measured_temp

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._ac.info.set_temp

    @property
    def fan_mode(self) -> str:
        """Return fan mode of this AC."""
        return AT2_TO_HA_FAN_SPEED[self._ac.info.fan_speed]

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return [AT2_TO_HA_FAN_SPEED[s] for s in self._ac.info.supported_fan_speeds]

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temp = int(kwargs.get(ATTR_TEMPERATURE, 0))
        if temp > 0:  # Only set if we have a valid temperature
            await self._ac.set_set_temp(temp)
            _LOGGER.debug("Set temperature to %d for AC %s", temp, self._ac.info.name)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._ac.set_fan_speed(HA_FAN_SPEED_TO_AT2[fan_mode])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            # Only turn off if currently active
            if self._ac.info.active:
                await self.async_turn_off()
        else:
            # Check if the mode is available in our conversion table
            if hvac_mode not in HA_MODE_TO_AT2:
                _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
                return
                
            # If AC is off, turn it on first, then set mode
            if not self._ac.info.active:
                await self.async_turn_on()
                # Wait a moment for the AC to turn on before setting mode
                await asyncio.sleep(0.5)
            
            # Set the mode (only if AC is on or we just turned it on)
            await self._ac.set_mode(HA_MODE_TO_AT2[hvac_mode])

    async def async_turn_on(self):
        """Turn on."""
        if not self._ac.info.active:
            await self._ac.turn_on()
            _LOGGER.debug("Turned on AC %s", self._ac.info.name)

    async def async_turn_off(self):
        """Turn off."""
        if self._ac.info.active:
            await self._ac.turn_off()
            _LOGGER.debug("Turned off AC %s", self._ac.info.name)

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        mode: ACMode = self._ac.info.mode

        # Dry mode supports no features
        if mode == ACMode.DRY:
            # only because there's no ClimateEntityFeature.NONE
            return ClimateEntityFeature.TARGET_TEMPERATURE

        # Fan mode doesn't support target temperature
        if mode == ACMode.FAN:
            return ClimateEntityFeature.FAN_MODE

        return ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE