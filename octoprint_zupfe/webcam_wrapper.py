import random
import urllib.parse

from .request import request_get
from .message_builder import max_safe_integer_js


class WebcamWrapper:
    def __init__(self, webcam, plugin):
        self._webcam = webcam
        self._plugin = plugin
        self._id = random.randint(1, max_safe_integer_js - 1)

    @property
    def id(self):
        return self._id

    @property
    def name(self) -> str:
        return self._webcam.config.displayName

    @property
    def can_snapshot(self) -> bool:
        return self._webcam.config.canSnapshot

    @property
    def can_stream(self) -> bool:
        return True

    @property
    def config(self) -> dict:
        webcam_config = self._webcam.config
        config = {
            'flip_h': webcam_config.flipH,
            'flip_v': webcam_config.flipV,
            'rotate_90': webcam_config.rotate90,
        }
        return config

    async def take_snapshot(self):
        if self.can_snapshot:
            config = self._webcam.config

            if self._webcam.config.compat is not None:
                snapshot_url = self.snapshot_url
                response = await request_get(snapshot_url, max_retries=1)
                data = await response.read()

                snapshot = {
                    'data': data,
                    'config': config
                }
                return snapshot

        return None

    @property
    def snapshot_url(self) -> str:
        snapshot_url = None
        if self._webcam.config.compat is not None:
            snapshot_url = self._webcam.config.compat.snapshot

        return snapshot_url

    @property
    def stream_url(self) -> str:
        mjpeg_url = self._webcam.config.extras['stream']

        # Parse the URL to check if it has protocol and host
        parsed_url = urllib.parse.urlparse(mjpeg_url)

        # If the URL doesn't have a scheme (protocol) or netloc (host),
        # prepend them from the plugin
        if not parsed_url.scheme or not parsed_url.netloc:
            # Assuming plugin has 'host' and 'port' attributes
            host_with_port = f"localhost:{self._plugin.port}"
            mjpeg_url = urllib.parse.urlunparse((parsed_url.scheme or "http", host_with_port, parsed_url.path,
                                                 parsed_url.params, parsed_url.query, parsed_url.fragment))

        return mjpeg_url
