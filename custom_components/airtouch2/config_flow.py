"""Config flow for airtouch2."""
import logging

from airtouch2 import AT2Client
import voluptuous as vol

from homeassistant import config_entries

from homeassistant.const import CONF_HOST

from .const import DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})

_LOGGER = logging.getLogger(__name__)


class Airtouch2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Airtouch2 config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        errors = {}

        host = user_input[CONF_HOST]
        self._async_abort_entries_match({CONF_HOST: host})

        airtouch2_client = AT2Client(host)
        _LOGGER.debug("Starting client in config_flow")

        if not airtouch2_client.start():
            # client could not connect
            errors["base"] = "cannot_connect"
        elif not airtouch2_client.aircons:
            errors["base"] = "no_units"

        # we only used the client to verify the config
        airtouch2_client.stop()

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )
        _LOGGER.debug("Config flow success")

        return self.async_create_entry(
            title=user_input[CONF_HOST],
            data={
                CONF_HOST: user_input[CONF_HOST],
            },
        )