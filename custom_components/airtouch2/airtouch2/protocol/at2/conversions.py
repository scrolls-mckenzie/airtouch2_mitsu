
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
        return supported_speeds[speed_val]
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
            brand = GATEWAYID_BRAND_LOOKUP[gateway_id]
            # Log if this is one of the unknown gateway IDs we're guessing at
            if gateway_id in [0xa7, 0xd3, 0xe5, 0xe9]:
                _LOGGER.info(f"Using gateway ID {hex(gateway_id)} with assumed brand {brand.name}. "
                           f"If AC control doesn't work properly, please report this gateway ID.")
            return brand
        else:
            # For ANY unknown gateway ID, use MITSUBISHI_ELECTRIC as safe default
            # This prevents system crashes and unresponsiveness
            _LOGGER.info(
                f"Unknown gateway ID {hex(gateway_id)} ({gateway_id} decimal) - using MITSUBISHI_ELECTRIC as safe default. "
                f"If AC control doesn't work properly, please report this gateway ID with your AC brand/model - " + OPEN_ISSUE_TEXT)
            return ACBrand.MITSUBISHI_ELECTRIC
    return None
