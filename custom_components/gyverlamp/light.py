import logging
import socket

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
    PLATFORM_SCHEMA,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_EFFECTS = "effects"

EFFECTS = [
    "Конфетти",
    "Огонь",
    "Радуга вертикальная",
    "Радуга горизонтальная",
    "Смена цвета",
    "Безумие",
    "Облака",
    "Лава",
    "Плазма",
    "Радуга",
    "Павлин",
    "Зебра",
    "Лес",
    "Океан",
    "Цвет",
    "Снег",
    "Матрица",
    "Светлячки",
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_EFFECTS): cv.ensure_list,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([GyverLamp(config)], True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    entity = GyverLamp(entry.options, entry.entry_id)
    async_add_entities([entity], True)

    hass.data[DOMAIN][entry.entry_id] = entity


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class GyverLamp(LightEntity):
    def __init__(self, config: dict, unique_id=None):
        self._attr_effect_list = config.get(CONF_EFFECTS, EFFECTS)
        self._attr_name = config.get(CONF_NAME, "Gyver Lamp")
        self._attr_should_poll = True
        self._attr_supported_color_modes = {ColorMode.HS}
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._attr_unique_id = unique_id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="@AlexGyver",
            model="GyverLamp",
        )

        self.host = config[CONF_HOST]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)

    @property
    def address(self) -> tuple:
        return self.host, 8888

    def debug(self, message):
        _LOGGER.debug(f"{self.host} | {message}")

    def turn_on(
        self,
        brightness: int = None,
        effect: str = None,
        hs_color: tuple = None,
        **kwargs,
    ):
        payload = []
        if brightness:
            payload.append("BRI%d" % brightness)

        if effect:
            try:
                payload.append("EFF%d" % self._attr_effect_list.index(effect))
            except ValueError:
                payload.append(effect)

        if hs_color:
            scale = round(hs_color[0] / 360.0 * 100.0)
            payload.append("SCA%d" % scale)
            speed = hs_color[1] / 100.0 * 255.0
            payload.append("SPD%d" % speed)

        if not self._attr_is_on:
            payload.append("P_ON")

        self.debug(f"SEND {payload}")

        for data in payload:
            self.sock.sendto(data.encode(), self.address)
            resp = self.sock.recv(1024)
            self.debug(f"RESP {resp}")

    def turn_off(self, **kwargs):
        self.sock.sendto(b"P_OFF", self.address)
        resp = self.sock.recv(1024)
        self.debug(f"RESP {resp}")

    def update(self):
        try:
            self.sock.sendto(b"GET", self.address)
            data = self.sock.recv(1024).decode().split(" ")
            self.debug(f"UPDATE {data}")
            # bri eff spd sca pow
            i = int(data[1])
            self._attr_effect = (
                self._attr_effect_list[i] if i < len(self._attr_effect_list) else None
            )
            self._attr_brightness = int(data[2])
            self._attr_hs_color = (
                float(data[4]) / 100.0 * 360.0,
                float(data[3]) / 255.0 * 100.0,
            )
            self._attr_is_on = data[5] == "1"
            self._attr_available = True

        except Exception as e:
            self.debug(f"Can't update: {e}")
            self._attr_available = False
