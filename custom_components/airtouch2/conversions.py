from airtouch2.at2 import ACFanSpeed, ACMode
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
}

AT2_TO_HA_FAN_SPEED = {
    ACFanSpeed.AUTO: FAN_AUTO,
    ACFanSpeed.QUIET: FAN_DIFFUSE,
    ACFanSpeed.LOW: FAN_LOW,
    ACFanSpeed.MEDIUM: FAN_MEDIUM,
    ACFanSpeed.HIGH: FAN_HIGH,
    ACFanSpeed.POWERFUL: FAN_FOCUS,
}

# inverse lookups
HA_MODE_TO_AT2 = {value: key for key, value in AT2_TO_HA_MODE.items()}
HA_FAN_SPEED_TO_AT2 = {value: key for key,
                       value in AT2_TO_HA_FAN_SPEED.items()}
