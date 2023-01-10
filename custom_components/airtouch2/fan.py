"""AirTouch 2 component to control AirTouch 2 Zones."""
from __future__ import annotations

import logging
from typing import Any

from airtouch2 import AT2Client, AT2Group

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AirTouch 2 group entities."""
    _LOGGER.debug("Setting up AirTouch 2 group entities")
    airtouch2_client: AT2Client = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for group in airtouch2_client.groups:
        group_entity = AirTouch2GroupEntity(airtouch2_client, group)
        entities.append(group_entity)

    if entities:
        async_add_entities(entities)
    _LOGGER.debug("fan::async_setup_entry complete")


class AirTouch2GroupEntity(FanEntity):
    """Representation of an AirTouch 2 zone."""

    def __init__(self, airtouch2_client: AT2Client, group: AT2Group) -> None:
        """Initialize the fan entity."""
        self._airtouch2_client = airtouch2_client
        self._group = group

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        # Add callback for when group receives new data
        # Removes callback on remove
        self.async_on_remove(self._group.add_callback(self.async_write_ha_state))
        _LOGGER.debug("fan::async_added_to_hass complete")

    # Properties
    @property
    def should_poll(self) -> bool:
        """Return whether the entity should poll."""
        return False

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"airtouch2_group_{self._group.number}"

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
    def name(self):
        """Return the name of this group."""
        return f"{self._group.name}"

    @property
    def is_on(self):
        """Return if group is on."""
        return self._group.on

    @property
    def supported_features(self) -> FanEntityFeature:
        """Fan supported features."""
        return FanEntityFeature.SET_SPEED

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 10

    @property
    def percentage(self) -> int:
        """Return current percentage of the group damper."""
        if not self._group.on:
            return 0
        return self._group.damp * 10

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

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the group."""
        if self._group.on:
            await self._group.turn_off()
