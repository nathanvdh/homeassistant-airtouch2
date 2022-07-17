"""AirTouch 2 component to control of AirTouch 2 Climate Devices."""
from __future__ import annotations

import logging
from typing import Callable

from airtouch2 import ACFanSpeed, ACMode, AT2Aircon, AT2Client

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS, PRECISION_WHOLE, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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
}

HA_MODE_TO_AT = {value: key for key, value in AT2_TO_HA_MODE.items()}
HA_FAN_SPEED_TO_AT2 = {value: key for key, value in AT2_TO_HA_FAN_SPEED.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Airtouch 2."""
    airtouch2_client = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[ClimateEntity] = [
        Airtouch2ACEntity(airtouch2_client, ac) for ac in airtouch2_client.aircons
    ]

    _LOGGER.debug(" Found entities %s", entities)
    async_add_entities(entities)



class Airtouch2ACEntity(ClimateEntity):
    """Representation of an AirTouch 2 ac."""

    def __init__(
        self, airtouch2_client: AT2Client, airtouch2_aircon: AT2Aircon
    ) -> None:
        """Initialize the climate device."""
        self._airtouch2_client = airtouch2_client
        self._ac = airtouch2_aircon

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        # Add callback for when client receives new data
        # Removes callback on remove
        self.async_on_remove(
            # TODO don't subscribe this single entity to ALL changes
            # i.e. Implement AC/Entity based callbacks rather than one list of callbacks for everything
            self._airtouch2_client.add_callback(self._on_new_data)
        )

    def _on_new_data(self) -> None:
        self.async_write_ha_state()

    # Properties
    @property
    def should_poll(self) -> bool:
        """Return whether the entity should poll."""
        return False
    @property
    def temperature_unit(self) -> str:
        return TEMP_CELSIUS

    @property
    def precision(self) -> float:
        return PRECISION_WHOLE

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer="Polyaire",
            model="Airtouch 2",
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"ac_{self._ac.number}"

    @property
    def name(self):
        """Return the name of the climate device."""
        return f"AC {self._ac.name}"

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._ac.ambient_temp

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._ac.set_temp

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        mode: ACMode = self._ac.mode

        # Dry mode supports no features
        if mode == ACMode.DRY:
            return 0

        # Fan mode doesn't support target temperature
        if mode == ACMode.FAN:
            return ClimateEntityFeature.FAN_MODE

        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    @property
    def fan_mode(self) -> str:
        """Return fan mode of this AC."""
        return AT2_TO_HA_FAN_SPEED[self._ac.fan_speed]

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return list(AT2_TO_HA_FAN_SPEED.values())

    @property
    def hvac_mode(self) -> str:
        """Return hvac target hvac state."""
        if not self._ac.on:
            return HVACMode.OFF

        return AT2_TO_HA_MODE[self._ac.mode]

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        return list(AT2_TO_HA_MODE.values()) + [HVACMode.OFF]

    # Methods
    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            self.turn_off()
        else:
            self._ac.set_mode(HA_MODE_TO_AT[hvac_mode])

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        self._ac.set_fan_speed(HA_FAN_SPEED_TO_AT2[fan_mode])

    def set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        self._ac.set_set_temp(int(temp))

    def turn_off(self):
        """Turn off."""
        self._ac.turn_off()

    def turn_on(self):
        """Turn on."""
        self._ac.turn_on()
