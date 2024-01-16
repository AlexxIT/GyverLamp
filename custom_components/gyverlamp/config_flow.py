import re

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from . import DOMAIN
from .light import CONF_EFFECTS, EFFECTS


def parse_effects(data: str) -> list:
    return re.split(r"\s*,\s*", data.strip())


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            host = user_input[CONF_HOST]
            user_input[CONF_EFFECTS] = parse_effects(user_input[CONF_EFFECTS])
            return self.async_create_entry(title=host, data=user_input)

        effects = ",".join(EFFECTS)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Optional(CONF_EFFECTS, default=effects): cv.string,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        host = self.config_entry.options[CONF_HOST]
        effects = ",".join(self.config_entry.options[CONF_EFFECTS])
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=host): cv.string,
                    vol.Optional(CONF_EFFECTS, default=effects): cv.string,
                }
            ),
        )

    async def async_step_user(self, user_input: dict = None):
        user_input[CONF_EFFECTS] = parse_effects(user_input[CONF_EFFECTS])
        return self.async_create_entry(title="", data=user_input)
