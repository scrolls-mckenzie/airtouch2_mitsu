from enum import IntEnum


class ACMode(IntEnum):
    AUTO = 0
    HEAT = 1
    DRY = 2
    FAN = 3
    COOL = 4
    # Mitsubishi Electric specific modes
    MITSUBISHI_MODE_130 = 130  # Unknown Mitsubishi mode - maps to HEAT for now
    MITSUBISHI_MODE_223 = 223  # Unknown Mitsubishi mode - maps to AUTO for now

    def __str__(self):
        return self._name_


class ACFanSpeed(IntEnum):
    AUTO = 0
    QUIET = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    POWERFUL = 5

    def __str__(self):
        return self._name_

# From adding AC2 on the panel and cycling through brands


class ACBrand(IntEnum):
    NONE = 0
    DAIKIN = 1
    FUJITSU = 2
    HITACHI = 3
    LG = 4
    MITSUBISHI_ELECTRIC = 5
    MITSUBISHI_HEAVY_IND = 6
    PANASONIC = 7
    SAMSUNG = 8
    TOSHIBA = 9
    # Unknown brand value encountered in the field
    UNKNOWN_168 = 168

    def __str__(self):
        return self._name_
