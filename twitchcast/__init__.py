"""
Send Twitch.TV streams to a Chromecast with chat enabled thanks to NightDev.

Uses http://nightdev.com/twitchcast/
"""
import asyncio
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pychromecast==1.0.3']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'twitchcast'

CONF_CHROMECAST_NAME = 'chromecast_name'
CONF_TWITCHCAST_CHANNEL = 'channel'
CONF_TWITCHCAST_LAYOUT = 'layout'
CONF_TWITCHCAST_LAYOUT_OPTIONS = ['right', 'left', 'top', 'bottom']

TWITCHCAST_CONTROLLER = 'TwitchCastController'

SERVICE_STREAM = 'cast_stream'
SERVICE_STREAM_SCHEMA = vol.Schema({
    vol.Required(CONF_TWITCHCAST_CHANNEL): cv.string,
    vol.Optional(CONF_TWITCHCAST_LAYOUT,
                 default=CONF_TWITCHCAST_LAYOUT_OPTIONS[0]):
    vol.In(CONF_TWITCHCAST_LAYOUT_OPTIONS),
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_CHROMECAST_NAME): cv.string,
        vol.Optional(CONF_TWITCHCAST_LAYOUT,
                     default=CONF_TWITCHCAST_LAYOUT_OPTIONS[0]):
        vol.In(CONF_TWITCHCAST_LAYOUT_OPTIONS),
    })
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    """Setup TwitchCast."""
    config = config.get(DOMAIN, {})

    from twitchcast import TwitchCastController
    tcc = TwitchCastController(config[CONF_CHROMECAST_NAME])
    tcc.setup()

    hass.data[DOMAIN] = {
        TWITCHCAST_CONTROLLER: tcc
    }

    @asyncio.coroutine
    def change_stream(call):
        """Change chromecast channel."""
        channel = call.data.get(CONF_TWITCHCAST_CHANNEL)
        layout = "chat-{}".format(call.data.get(CONF_TWITCHCAST_LAYOUT))
        _LOGGER.info("twitchcasting {} - {}".format(channel, layout))
        hass.data[DOMAIN][TWITCHCAST_CONTROLLER].stream_channel(
            channel=channel, layout=layout)

    hass.services.async_register(
        DOMAIN, SERVICE_STREAM, change_stream,
        schema=SERVICE_STREAM_SCHEMA)

    return True
