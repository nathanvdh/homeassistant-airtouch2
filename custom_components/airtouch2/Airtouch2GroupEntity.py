from airtouch2 import At2Group

from typing import Any, final
import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.airtouch2.const import DOMAIN
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)

@final
class AirTouch2GroupEntity(FanEntity):
    """Representation of an AirTouch 2 zone."""

    #
    # Entity attributes:
    #
    _attr_should_poll: bool = False


    def __init__(self, group: At2Group) -> None:
        """Initialize the fan entity."""
        self._group = group

    #
    # Entity overrides:
    #

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"airtouch2_group_{self._group.number}"

    @property
    def name(self):
        """Return the name of this group."""
        return f"{self._group.name}"

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
        # Add callback for when group receives new data
        # Removes callback on remove
        self.async_on_remove(
            self._group.add_callback(self.async_write_ha_state))
        _LOGGER.debug("fan::async_added_to_hass complete")


    #
    # FanEntity overrides
    #

    async def async_set_percentage(self, percentage: int):
        """Set the percentage of the group damper."""
        if percentage == 0:
            # We don't need to do anything because FanEntity already calls turn_off
            return
        damp = int(percentage / 10)
        # clamp between 1 and 10
        damp = max(min(damp, 10), 1)
        await self._group.set_damp(damp)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the group."""
        if not self._group.on:
            await self._group.turn_on()
        if percentage:
            await self.async_set_percentage(percentage)

    @property
    def is_on(self):
        """Return if group is on."""
        return self._group.on

    @property
    def percentage(self) -> int:
        """Return current percentage of the group damper."""
        if not self._group.on:
            return 0
        return self._group.damp * 10

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 10

    @property
    def supported_features(self) -> FanEntityFeature:
        """Fan supported features."""
        return FanEntityFeature.SET_SPEED

    #
    # ToggleEntity overrides:
    #

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the group."""
        if self._group.on:
            await self._group.turn_off()
