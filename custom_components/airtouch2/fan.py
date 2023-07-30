"""AirTouch 2 component to control AirTouch 2 Zones."""
from __future__ import annotations
import logging
from pprint import pprint

from airtouch2.at2 import At2Client
from .Airtouch2GroupEntity import AirTouch2GroupEntity
from .const import DOMAIN


from homeassistant.components.fan import FanEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AirTouch 2 group entities."""
    _LOGGER.debug("Setting up AirTouch 2 group entities")
    airtouch2_client: At2Client = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[FanEntity] = [
        AirTouch2GroupEntity(group) for group in airtouch2_client.groups_by_id.values()
    ]

    if entities:
        async_add_entities(entities)
