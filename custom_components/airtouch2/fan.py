"""AirTouch 2 component to control AirTouch 2 Zones."""
from __future__ import annotations

from airtouch2 import At2Client

import logging
from typing import Any

from homeassistant.components.airtouch2.Airtouch2GroupEntity import AirTouch2GroupEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    airtouch2_client: At2Client = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for group in airtouch2_client.groups:
        group_entity = AirTouch2GroupEntity(group)
        entities.append(group_entity)

    if entities:
        async_add_entities(entities)
    _LOGGER.debug("fan::async_setup_entry complete")
