from __future__ import annotations
import logging

from airtouch2 import AT2Client, AT2Group

from .const import DOMAIN

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AirTouch 2 group entities"""
    _LOGGER.debug("Setting up AirTouch 2 group entities...")
    airtouch2_client: AT2Client = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for group in airtouch2_client.groups:
        group_entity = AirTouch2GroupEntity(airtouch2_client, group)
        entities.append(group_entity)

    if entities:
        async_add_entities(entities)

class AirTouch2GroupEntity(FanEntity):
    def __init__(self, airtouch2_client: AT2Client, group: AT2Group):
        """Initialize the fan entity."""
        self._airtouch2_client = airtouch2_client
        self._group = group

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
        """Return the name of this device."""
        return f"{self._group.name}"

    @property
    def is_on(self):
        """Return if group is on"""
        return self._group.on

    @property
    def supported_features(self) -> int:
        """Fan supported features."""
        return FanEntityFeature.SET_SPEED

    @property
    def speed_count(self) -> int:
        return 10

    @property
    def percentage(self) -> int:
        """Return current percentage of fan"""
        if not self._group.on:
            return 0
        return self._group.damp*10

    def set_percentage(self, percentage: int):
        if percentage == 0:
            # We don't need to do anything becaus FanEntity already calls turn_off
            return
        damp = int(percentage/10)
        # clamp between 1 and 10
        damp = max(min(damp, 10), 1)
        self._group.set_damp(damp)

    def turn_on(self, **kwargs):
        if not self._group.on:
            self._group.turn_on()

    def turn_off(self, **kwargs):
        if self._group.on:
            self._group.turn_off()

