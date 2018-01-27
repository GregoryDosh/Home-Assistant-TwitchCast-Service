"""
Start Twitch.TV streams with chat on your Chromecast using TwitchCast.

Uses servers provided by http://nightdev.com/twitchcast/ for stream and chat
"""
import json
import logging
import pychromecast
import random
import requests
import sys
import time
from functools import partial
from pychromecast import get_chromecasts, Chromecast
from pychromecast.controllers import BaseController

REQUIREMENTS = ['pychromecast==1.0.3']

__version__ = '0.1.1'

_LOGGER = logging.getLogger(__name__)


class TwitchCastController(BaseController):
    """Controller used to send TwitchCast streams to a Chromecast."""

    def __init__(self,
                 chromecast_name: str=None,
                 chromecast_host: str=None) -> None:
        """Take care of some house keeping on init."""
        super(TwitchCastController, self).__init__(
            'urn:x-cast:com.google.cast.media', 'DAC1CD8C')
        self._cast = None  # type: Chromecast
        self._chromecast_host = chromecast_host
        self._chromecast_name = chromecast_name
        self._expected_app_id = 'DAC1CD8C'
        self._headers = {
            'User-Agent': "Home-Assistant-TwitchCast-Service {}"
                          .format(__version__)
        }
        self._selected_location = None  # type: str
        self._setup_valid = False

    def _setup(self) -> bool:
        self._setup_valid = self._setup_chromecast() and \
            self._setup_locations()
        if self._setup_valid:
            _LOGGER.info("setup completed successfully")
        else:
            _LOGGER.warning("setup failed")
            if not self._cast:
                _LOGGER.warning("no cast device")
            if not self._selected_location:
                _LOGGER.warning("no location")
            return False
        return True

    def _setup_chromecast(self) -> bool:
        if self._chromecast_host:
            try:
                self._cast = Chromecast(host=self._chromecast_host)
                self._cast.register_handler(self)
                return True
            except pychromecast.error.ChromecastConnectionError:
                _LOGGER.error("cannot find {}".format(self._chromecast_host))
        elif self._chromecast_name:
            try:
                self._cast = next(cc for cc in get_chromecasts() if
                                  cc.device.friendly_name ==
                                  self._chromecast_name)
                self._cast.register_handler(self)
                return True
            except StopIteration:
                _LOGGER.error("cannot find {}".format(self._chromecast_name))
        else:
            _LOGGER.error("no chromecast host or name defined.")
        return False

    def _setup_locations(self) -> bool:
        r = requests.get('http://nightdev.com/twitchcast/pops.json?{}'.format(
            random.random()), headers=self._headers)
        locations = []  # type: List[Dict[str, Dict[str, object]]]
        if r.status_code == 200:
            try:
                locations = json.loads(r.text)
            except ValueError:
                _LOGGER.error("error parsing populations")
        updated_locations = []
        for location in locations:
            r = requests.get('{}/stats?callback=?'.format(location['url']),
                             headers=self._headers)
            if r.status_code == 200:
                try:
                    location['status'] = json.loads(r.text[2:-2])
                    location['status']['latency'] = r.elapsed
                except ValueError:
                    continue
                updated_locations.append(location)
        if updated_locations:
            self._selected_location = sorted(
                updated_locations, key=lambda x: x['status']['latency']
            )[0]['url']
            return True
        return False

    @property
    def _location(self) -> str:
        """Get selected location or find one if needed."""
        if not self._selected_location:
            self._setup_locations()
        return self._selected_location

    @property
    def cast(self) -> Chromecast:
        """Get chromecast object or set one up if needed."""
        if not self._setup_valid:
            self._setup()
        return self._cast

    def _get_content_id(self, channel: str) -> str:
        _LOGGER.debug("getting content_id for {}".format(channel))
        r = requests.get('http://nightdev.com/twitchcast/token.php?channel={}'.
                         format(requests.utils.quote(channel)),
                         headers=self._headers)
        token, sig = "", ""
        if r.status_code == 200:
            try:
                parsed_text = json.loads(r.text)
                token = parsed_text['token']
                sig = parsed_text['sig']
            except (ValueError, KeyError):
                _LOGGER.error("error parsing token and sig for {}".
                              format(channel))
                return ""
        else:
            _LOGGER.error("status {} during token and sig for {}".format(
                r.status_code, channel))
        playlist = []  # type: List[dict]
        if token and sig:
            url = '{}/get/playlist?channel={}&token={}&sig={}&callback=?'.\
                format(
                    self._location,
                    requests.utils.quote(channel),
                    requests.utils.quote(token),
                    requests.utils.quote(sig))
            r = requests.get(url, headers=self._headers)
            if r.status_code == 200:
                try:
                    playlist = json.loads(r.text[2:-2])['playlist']
                except ValueError:
                    _LOGGER.error("error parsing playlist for {}".
                                  format(channel))
                    return ""
            else:
                _LOGGER.error("status {} during playlist for {}".format(
                    r.status_code, channel))
        else:
            return ""
        if playlist:
            return playlist[0]['url']
        else:
            return ""

    def _check_app_id(self, timeout: int=10) -> bool:
        if self.cast.app_id != self._expected_app_id:
            self.launch()
        for t in range(timeout * 5):
            if self.cast.app_id != self._expected_app_id:
                time.sleep(t / 5)
            else:
                return True
        return False

    def _stream_channel_callback(self,
                                 channel: str,
                                 layout: str,
                                 content_id: str) -> None:
        msg = {
            'type': 'LOAD',
            'media': {
                'contentId': content_id,
                'contentType': 'video/mp4',
                'streamType': 'LIVE',
                'metadata': self.channel_details(channel)
            },
            'mediaSessionId': None,
            'customData': {
                'channel': channel,
                'layout': layout,
            },
        }
        _LOGGER.debug("sending chromecast message {}".format(msg))
        self.send_message(msg)

    def channel_details(self, channel: str) -> dict:
        """Get stream title & details from Twitch Kraken API."""
        _LOGGER.debug("getting steam details for {}".format(channel))
        metadata = {
            'metadataType': 1,
            'title': channel,
            'subtitle': channel,
            'images': []
        }
        r = requests.get('https://api.twitch.tv/kraken/streams/{}?client_id'
                         '=apbhlybpld3ybc6grv5c118xqpoz01c'.
                         format(requests.utils.quote(channel)),
                         headers=self._headers)
        if r.status_code == 200:
            try:
                parsed_text = json.loads(r.text)['stream']['channel']
                metadata['title'] = parsed_text['display_name']
                metadata['subtitle'] = parsed_text['status']
                metadata['images'].append({
                                          'url': parsed_text['logo'],
                                          'width': 0,
                                          'height': 0,
                                          })
            except (ValueError, KeyError):
                _LOGGER.error("error parsing channel details for {}".
                              format(channel))
        else:
            _LOGGER.error("status {} during token and sig for {}".format(
                r.status_code, channel))
        return metadata

    def stream_channel(self, channel: str, layout: str) -> None:
        """Stream a channel for a given layout on the Chromecast."""
        _LOGGER.debug("trying to stream {} - {}".format(channel, layout))
        content_id = self._get_content_id(channel)
        self._launched = False
        if content_id:
            _LOGGER.debug("launching {} - {}".format(channel, layout))
            if self._check_app_id():
                self.launch(callback_function=partial(
                            self._stream_channel_callback,
                            channel=channel,
                            layout=layout,
                            content_id=content_id))
            else:
                _LOGGER.warning("timed out waiting on chromecast")
        else:
            _LOGGER.warning("couldn't get content_id for {}".format(channel))

if __name__ == '__main__':
    if len(sys.argv) == 3:
        tc = TwitchCastController(chromecast_host='Chromecast-Ultra')
        tc.stream_channel(sys.argv[1], sys.argv[2])
