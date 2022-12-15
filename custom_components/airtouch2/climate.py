"""AirTouch 2 component to control AirTouch 2 Climate Device."""
from __future__ import annotations

import logging

from airtouch2 import ACFanSpeedReference, ACMode, AT2Aircon, AT2Client

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
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
    ACFanSpeedReference.AUTO: FAN_AUTO,
    ACFanSpeedReference.QUIET: FAN_DIFFUSE,
    ACFanSpeedReference.LOW: FAN_LOW,
    ACFanSpeedReference.MEDIUM: FAN_MEDIUM,
    ACFanSpeedReference.HIGH: FAN_HIGH,
    ACFanSpeedReference.POWERFUL: FAN_FOCUS,
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

    _LOGGER.debug(f" Found entities {entities}")
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

    @property
    def should_poll(self) -> bool:
        """Return whether the entity should poll."""
        return False

    @property
    def temperature_unit(self) -> str:
        """Return the unit of temperature measurement for the system."""
        return TEMP_CELSIUS

    @property
    def precision(self) -> float:
        """Return the precision of the temperature in the system."""
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
        return self._ac.measured_temp

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._ac.set_temp

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        mode: ACMode = self._ac.mode

        # Dry mode supports no features
        if mode == ACMode.DRY:
            # return 0
            # only because there's no ClimateEntityFeature.NONE
            return ClimateEntityFeature.TARGET_TEMPERATURE

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
        return [AT2_TO_HA_FAN_SPEED[s] for s in self._ac.supported_fan_speeds]

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

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            if self._ac.on:
                await self.async_turn_off()
        else:
            if not self._ac.on:
                await self.async_turn_on()
            await self._ac.set_mode(HA_MODE_TO_AT[hvac_mode])

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._ac.set_fan_speed(HA_FAN_SPEED_TO_AT2[fan_mode])

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temp = int(kwargs.get(ATTR_TEMPERATURE, 0))
        await self._ac.set_set_temp(temp)

    async def async_turn_off(self):
        """Turn off."""
        await self._ac.turn_off()

    async def async_turn_on(self):
        """Turn on."""
        await self._ac.turn_on()
