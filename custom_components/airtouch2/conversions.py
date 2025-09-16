from .airtouch2.protocol.at2.enums import ACFanSpeed, ACMode
from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACMode
)


AT2_TO_HA_MODE = {
    ACMode.AUTO: HVACMode.HEAT_COOL,
    ACMode.HEAT: HVACMode.HEAT,
    ACMode.DRY: HVACMode.DRY,
    ACMode.FAN: HVACMode.FAN_ONLY,
    ACMode.COOL: HVACMode.COOL,
    ACMode.MITSUBISHI_MODE_130: HVACMode.HEAT,  # Map unknown Mitsubishi mode to HEAT
}

AT2_TO_HA_FAN_SPEED = {
    ACFanSpeed.AUTO: FAN_AUTO,
    ACFanSpeed.QUIET: FAN_DIFFUSE,
    ACFanSpeed.LOW: FAN_LOW,
    ACFanSpeed.MEDIUM: FAN_MEDIUM,
    ACFanSpeed.HIGH: FAN_HIGH,
    ACFanSpeed.POWERFUL: FAN_FOCUS,
}

# inverse lookups - handle duplicates properly
HA_MODE_TO_AT2 = {
    HVACMode.HEAT_COOL: ACMode.AUTO,
    HVACMode.HEAT: ACMode.HEAT,  # Prefer standard HEAT over Mitsubishi mode 130
    HVACMode.DRY: ACMode.DRY,
    HVACMode.FAN_ONLY: ACMode.FAN,
    HVACMode.COOL: ACMode.COOL,
}

HA_FAN_SPEED_TO_AT2 = {value: key for key,
                       value in AT2_TO_HA_FAN_SPEED.items()}