
import logging
from .constants import OPEN_ISSUE_TEXT
from typing import Optional
from .enums import ACBrand, ACFanSpeed
from .lookups import GATEWAYID_BRAND_LOOKUP

_LOGGER = logging.getLogger(__name__)


def fan_speed_from_val(supported_speeds: list[ACFanSpeed], speed_val: int) -> ACFanSpeed:
    if speed_val < 5:
        # Units with no Auto speed still start with low == 1
        if ACFanSpeed.AUTO not in supported_speeds:
            speed_val -= 1
        
        # Ensure we don't go out of bounds
        if 0 <= speed_val < len(supported_speeds):
            return supported_speeds[speed_val]
        else:
            _LOGGER.warning(f"Fan speed value {speed_val} out of bounds for supported speeds {supported_speeds}, defaulting to first available speed")
            return supported_speeds[0] if supported_speeds else ACFanSpeed.AUTO
    else:
        return ACFanSpeed.AUTO


def val_from_fan_speed(supported_speeds: list[ACFanSpeed], speed: ACFanSpeed):
    speed_val = supported_speeds.index(speed)
    # Units with no Auto speed still start with low == 1
    if ACFanSpeed.AUTO not in supported_speeds:
        speed_val += 1
    return speed_val


def brand_from_gateway_id(gateway_id: int) -> Optional[ACBrand]:
    if gateway_id > 0:
        if gateway_id in GATEWAYID_BRAND_LOOKUP:
            return GATEWAYID_BRAND_LOOKUP[gateway_id]
        else:
            _LOGGER.warning(
                f"AC has an unfamiliar gateway ID: {hex(gateway_id)} - " + OPEN_ISSUE_TEXT +
                "\nInclude the gateway ID shown above")
    return None
