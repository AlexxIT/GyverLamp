from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "gyverlamp"


async def async_setup(hass, hass_config):
    # used only with GUI setup
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # migrate data (after first setup) to options
    if entry.data:
        hass.config_entries.async_update_entry(entry, data={}, options=entry.data)

    # add options handler
    entry.add_update_listener(async_update_options)

    # forward to light setup
    coro = hass.config_entries.async_forward_entry_setup(entry, "light")
    hass.async_create_task(coro)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    # update entity config
    hass.data[DOMAIN][entry.entry_id].update_config(entry.options)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return await hass.config_entries.async_forward_entry_unload(entry, "light")
