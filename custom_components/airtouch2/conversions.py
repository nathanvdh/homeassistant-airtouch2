from airtouch2.at2 import ACFanSpeedReference, ACMode
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
    ACFanSpeedReference.AUTO: FAN_AUTO,
    ACFanSpeedReference.QUIET: FAN_DIFFUSE,
    ACFanSpeedReference.LOW: FAN_LOW,
    ACFanSpeedReference.MEDIUM: FAN_MEDIUM,
    ACFanSpeedReference.HIGH: FAN_HIGH,
    ACFanSpeedReference.POWERFUL: FAN_FOCUS,
}

# inverse lookups
HA_MODE_TO_AT2 = {value: key for key, value in AT2_TO_HA_MODE.items()}
HA_FAN_SPEED_TO_AT2 = {value: key for key,
                       value in AT2_TO_HA_FAN_SPEED.items()}
