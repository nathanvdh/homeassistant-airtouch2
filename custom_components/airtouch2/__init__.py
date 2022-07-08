"""The airtouch2 integration."""
from __future__ import annotations

import logging

from airtouch2 import AT2Client

from homeassistant.config_entries import ConfigEntry

from homeassistant.const import CONF_HOST, Platform, EVENT_HOMEASSISTANT_STOP

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.CLIMATE]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up airtouch2 from a config entry."""
    # not sure if this line is necessary?
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    airtouch2_client = AT2Client(host)

    if not airtouch2_client.start():
        raise ConfigEntryNotReady("Airtouch2 client failed to start - check logs")
    if not airtouch2_client.aircons:
        # no ACs found
        raise ConfigEntryNotReady("No AC units were found")

    hass.data[DOMAIN][entry.entry_id] = airtouch2_client

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unload entry called")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        _LOGGER.debug("unload okay entered")
        hass.data[DOMAIN][entry.entry_id].stop()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok