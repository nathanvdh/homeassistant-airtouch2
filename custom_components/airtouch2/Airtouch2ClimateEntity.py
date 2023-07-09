
from airtouch2 import At2Aircon, ACMode
from .conversions import AT2_TO_HA_FAN_SPEED, AT2_TO_HA_MODE, HA_MODE_TO_AT2, HA_FAN_SPEED_TO_AT2
from .const import DOMAIN

from typing import final

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    UnitOfTemperature,
    ATTR_TEMPERATURE,
    PRECISION_WHOLE
)
from homeassistant.helpers.entity import DeviceInfo


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
        self._ac = airtouch2_aircon

    #
    # Entity overrides:
    #

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"at2_ac_{self._ac.number}"

    @property
    def name(self):
        """Return the name of the entity."""
        return f"AC {self._ac.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer="Polyaire",
            model="Airtouch 2",
        )

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        # Add callback for when aircon receives new data
        # Removes callback on remove
        self.async_on_remove(self._ac.add_callback(self.async_write_ha_state))

    #
    # ClimateEntity overrides:
    #

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        if not self._ac.on:
            return HVACMode.OFF

        return AT2_TO_HA_MODE[self._ac.mode]

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return list(AT2_TO_HA_MODE.values()) + [HVACMode.OFF]

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._ac.measured_temp

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._ac.set_temp

    @property
    def fan_mode(self) -> str:
        """Return fan mode of this AC."""
        return AT2_TO_HA_FAN_SPEED[self._ac.fan_speed]

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return [AT2_TO_HA_FAN_SPEED[s] for s in self._ac.supported_fan_speeds]

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temp = int(kwargs.get(ATTR_TEMPERATURE, 0))
        await self._ac.set_set_temp(temp)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._ac.set_fan_speed(HA_FAN_SPEED_TO_AT2[fan_mode])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            if self._ac.on:
                await self.async_turn_off()
        else:
            if not self._ac.on:
                await self.async_turn_on()
            await self._ac.set_mode(HA_MODE_TO_AT2[hvac_mode])

    async def async_turn_on(self):
        """Turn on."""
        await self._ac.turn_on()

    async def async_turn_off(self):
        """Turn off."""
        await self._ac.turn_off()

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        mode: ACMode = self._ac.mode

        # Dry mode supports no features
        if mode == ACMode.DRY:
            # only because there's no ClimateEntityFeature.NONE
            return ClimateEntityFeature.TARGET_TEMPERATURE

        # Fan mode doesn't support target temperature
        if mode == ACMode.FAN:
            return ClimateEntityFeature.FAN_MODE

        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
