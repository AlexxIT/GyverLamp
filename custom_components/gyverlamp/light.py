import logging
import random
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
CONF_RANDOM_EFFECTS = 'random_effects'
CONF_USE_RANDOM_EFFECT = 'use_random_effect'
CONF_INCLUDE_ALL_EFFECT_TO_RANDOM = 'include_all_effect_to_random'
CONF_EFFECTS_MAP = 'effects_map'
CONF_EFFECTS_MAP_NAME = 'name'
CONF_EFFECTS_MAP_ID = 'id'
CONF_EFFECTS_MAP_RANDOM = 'random'

EFFECTS = ["Конфетти", "Огонь", "Радуга вертикальная", "Радуга горизонтальная",
           "Смена цвета", "Безумие", "Облака", "Лава", "Плазма", "Радуга",
           "Павлин", "Зебра", "Лес", "Океан", "Цвет", "Снег", "Матрица",
           "Светлячки"]

EFFECT_MAP_ITEM = vol.Schema({
    vol.Required(CONF_EFFECTS_MAP_NAME): cv.string,
    vol.Required(CONF_EFFECTS_MAP_ID): cv.positive_int,
    vol.Optional(CONF_EFFECTS_MAP_RANDOM, default=False): cv.boolean
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_USE_RANDOM_EFFECT): cv.boolean,
    vol.Optional(CONF_INCLUDE_ALL_EFFECT_TO_RANDOM): cv.boolean,
    vol.Optional(CONF_EFFECTS): cv.ensure_list,
    vol.Optional(CONF_EFFECTS_MAP): vol.All(cv.ensure_list, [EFFECT_MAP_ITEM])
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
    _available = False
    _brightness = None
    _effect = None
    _host = None
    _hs_color = None
    _is_on = None
    _effects_by_name = dict()
    _effects_by_id = dict()
    _use_random_effect = None
    _random_effect_ids = None

    def __init__(self, config: dict, unique_id=None):
        self._name = config.get(CONF_NAME, "Gyver Lamp")
        self._unique_id = unique_id

        self.update_config(config)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)

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
        return list(self._effects_by_id.values())

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
    def available(self):
        return self._available

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

    def debug(self, message):
        _LOGGER.debug(f"{self._host} | {message}")

    def update_config(self, config: dict):
        self._host = config[CONF_HOST]
        self._use_random_effect = config.get(CONF_USE_RANDOM_EFFECT, False)

        effects_list = config.get(CONF_EFFECTS, EFFECTS)
        effects_map = config.get(CONF_EFFECTS_MAP, {})

        self._effects_by_id = {i: effects_list[i] for i in range(0, len(effects_list))}

        random_ids = set()
        if config.get(CONF_INCLUDE_ALL_EFFECT_TO_RANDOM, False):
            random_ids.update(list(self._effects_by_id.keys()))

        for effect_info in effects_map:
            effect_id = effect_info.get(CONF_EFFECTS_MAP_ID, 0)
            self._effects_by_id[effect_id] = effect_info.get(CONF_EFFECTS_MAP_NAME, "none")
            if effect_info.get(CONF_EFFECTS_MAP_RANDOM, False):
                random_ids.add(effect_id)

        self._effects_by_name = {}
        for item in self._effects_by_id.items():
            self._effects_by_name[item[1]] = item[0]

        for item in config.get(CONF_RANDOM_EFFECTS, []):
            if item in self._effects_by_name:
                random_ids.add(self._effects_by_name[item])

        self._random_effect_ids = []
        if self._use_random_effect and len(random_ids) > 0:
            self._random_effect_ids.extend(list(random_ids))

        self.debug("map " + str(self._effects_by_name))
        self.debug("_random_effect_ids " + str(self._random_effect_ids))

        if self.hass:
            self._async_write_ha_state()

    def turn_on(self, **kwargs):
        payload = []
        if ATTR_BRIGHTNESS in kwargs:
            payload.append('BRI%d' % kwargs[ATTR_BRIGHTNESS])

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            try:
                if effect in self._effects_by_name:
                    payload.append('EFF%d' % self._effects_by_name[effect])
                else:
                    payload.append(effect)
            except ValueError:
                payload.append(effect)
        elif self._use_random_effect and len(self._random_effect_ids) > 0:
            payload.append('EFF%d' % random.choice(self._random_effect_ids))

        if ATTR_HS_COLOR in kwargs:
            scale = round(kwargs[ATTR_HS_COLOR][0] / 360.0 * 100.0)
            payload.append('SCA%d' % scale)
            speed = kwargs[ATTR_HS_COLOR][1] / 100.0 * 255.0
            payload.append('SPD%d' % speed)

        if not self.is_on:
            payload.append('P_ON')

        self.debug(f"SEND {payload}")

        for data in payload:
            self.sock.sendto(data.encode(), self.address)
            resp = self.sock.recv(1024)
            self.debug(f"RESP {resp}")

    def turn_off(self, **kwargs):
        self.sock.sendto(b'P_OFF', self.address)
        resp = self.sock.recv(1024)
        self.debug(f"RESP {resp}")

    def update(self):
        try:
            self.sock.sendto(b'GET', self.address)
            data = self.sock.recv(1024).decode().split(' ')
            self.debug(f"UPDATE {data}")
            # bri eff spd sca pow
            i = int(data[1])
            self._effect = self._effects_by_id.get(i, None)
            self._brightness = int(data[2])
            self._hs_color = (float(data[4]) / 100.0 * 360.0,
                              float(data[3]) / 255.0 * 100.0)
            self._is_on = data[5] == '1'
            self._available = True

        except Exception as e:
            self.debug(f"Can't update: {e}")
            self._available = False
