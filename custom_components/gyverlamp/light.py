import logging
import socket

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity, \
    SUPPORT_BRIGHTNESS, SUPPORT_EFFECT, SUPPORT_COLOR, ATTR_BRIGHTNESS, \
    ATTR_EFFECT, ATTR_HS_COLOR
from homeassistant.const import CONF_HOST

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string
})

EFFECTS = ["Конфетти", "Огонь", "Радуга вертикальная", "Радуга горизонтальная",
           "Смена цвета", "Безумие", "Облака", "Лава", "Плазма", "Радуга",
           "Павлин", "Зебра", "Лес", "Океан", "Цвет", "Снег", "Матрица",
           "Светлячки"]
FEATURES = SUPPORT_BRIGHTNESS | SUPPORT_EFFECT | SUPPORT_COLOR


def setup_platform(hass, config, add_entities, discovery_info=None):
    host = config[CONF_HOST]
    add_entities([GyverLamp(host)])


class GyverLamp(LightEntity):
    def __init__(self, host: str, port: int = 8888):
        self.address = (host, port)

        self._effect = None
        self._brightness = None
        self._hs_color = None
        self._is_on = None

    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        return "Gyver Lamp"

    @property
    def brightness(self):
        return self._brightness

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def effect_list(self):
        return EFFECTS

    @property
    def effect(self):
        return self._effect

    @property
    def supported_features(self):
        return FEATURES

    @property
    def is_on(self):
        return self._is_on

    def turn_on(self, **kwargs):
        self.update()

        payload = []
        if ATTR_BRIGHTNESS in kwargs:
            payload.append('BRI%d' % kwargs[ATTR_BRIGHTNESS])

        if ATTR_EFFECT in kwargs:
            payload.append('EFF%d' % EFFECTS.index(kwargs[ATTR_EFFECT]))

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
            self._effect = EFFECTS[int(data[1])]
            self._brightness = int(data[2])
            self._hs_color = (float(data[4]) / 100.0 * 360.0,
                              float(data[3]) / 255.0 * 100.0)
            self._is_on = data[5] == '1'
        except:
            pass
