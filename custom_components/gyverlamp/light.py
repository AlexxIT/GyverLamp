import logging
import socket

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity, \
    SUPPORT_BRIGHTNESS, SUPPORT_EFFECT, SUPPORT_COLOR, ATTR_BRIGHTNESS, \
    ATTR_EFFECT, ATTR_HS_COLOR
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_EFFECTS = 'effects'

EFFECTS = ["Конфетти", "Огонь", "Радуга вертикальная", "Радуга горизонтальная",
           "Смена цвета", "Безумие", "Облака", "Лава", "Плазма", "Радуга",
           "Павлин", "Зебра", "Лес", "Океан", "Цвет", "Снег", "Матрица",
           "Светлячки"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_EFFECTS): cv.ensure_list
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([GyverLamp(config)], True)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities):
    entity = GyverLamp(entry.options, entry.entry_id)
    async_add_entities([entity], True)

    hass.data[DOMAIN][entry.entry_id] = entity


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class GyverLamp(LightEntity):
    _brightness = None
    _effect = None
    _effects = None
    _host = None
    _hs_color = None
    _is_on = None

    def __init__(self, config: dict, unique_id=None):
        self._name = config.get(CONF_NAME, "Gyver Lamp")
        self._unique_id = unique_id

        self.update_config(config)

    @property
    def should_poll(self):
        return True

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def brightness(self):
        return self._brightness

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def effect_list(self):
        return self._effects

    @property
    def effect(self):
        return self._effect

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_EFFECT | SUPPORT_COLOR

    @property
    def is_on(self):
        return self._is_on

    @property
    def device_info(self):
        """
        https://developers.home-assistant.io/docs/device_registry_index/
        """
        return {
            'identifiers': {(DOMAIN, self._unique_id)},
            'manufacturer': "@AlexGyver",
            'model': "GyverLamp"
        }

    @property
    def address(self) -> tuple:
        return self._host, 8888

    def update_config(self, config: dict):
        self._effects = config.get(CONF_EFFECTS, EFFECTS)
        self._host = config[CONF_HOST]

        if self.hass:
            self._async_write_ha_state()

    def turn_on(self, **kwargs):
        self.update()

        payload = []
        if ATTR_BRIGHTNESS in kwargs:
            payload.append('BRI%d' % kwargs[ATTR_BRIGHTNESS])

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            payload.append('EFF%d' % self._effects.index(effect))

        if ATTR_HS_COLOR in kwargs:
            scale = round(kwargs[ATTR_HS_COLOR][0] / 360.0 * 100.0)
            payload.append('SCA%d' % scale)
            speed = kwargs[ATTR_HS_COLOR][1] / 100.0 * 255.0
            payload.append('SPD%d' % speed)

        if not self.is_on:
            payload.append('P_ON')

        _LOGGER.debug("SEND %s", payload)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for data in payload:
            sock.sendto(data.encode(), self.address)
            resp = sock.recv(1024)
            _LOGGER.debug("RESP %s", resp)

    def turn_off(self, **kwargs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b'P_OFF', self.address)
        resp = sock.recv(1024)
        _LOGGER.debug("RESP %s", resp)

    def update(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.sendto(b'GET', self.address)
            data = sock.recv(1024).decode().split(' ')
            _LOGGER.debug("UPDATE %s", data)
            # bri eff spd sca pow
            i = int(data[1])
            self._effect = self._effects[i] if i < len(self._effects) else None
            self._brightness = int(data[2])
            self._hs_color = (float(data[4]) / 100.0 * 360.0,
                              float(data[3]) / 255.0 * 100.0)
            self._is_on = data[5] == '1'
        except:
            pass
