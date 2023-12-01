import logging

from .request import request_get, request
from .websocket import WebSocketClient

logger = logging.getLogger("octoprint.plugins.zupfe.backend")


class Backend:
    def __init__(self, backend_url, frontend_url):
        self.octo_id = None
        self.api_key = None
        self.urls = None
        self._ws = None
        self.backendUrl = backend_url
        self.frontend_url = frontend_url

        # FIXME hardcoded url
        self.backend_ws_url = backend_url.replace('https://', 'wss://') + '/api/v1/printers'

    async def request(self, method, url, headers=None, data=None, max_retries=float('inf')):
        if headers is None:
            headers = {}

        headers = {**headers, "x-api-key": self.api_key}
        return await request(method, url, headers=headers, data=data, max_retries=max_retries)

    def is_initialized(self):
        return self.urls is not None and self.octo_id is not None

    def is_connected(self):
        return self._ws is not None and self._ws.is_connected()

    async def init(self):
        logger.debug('Fetching api urls')
        response = await request_get(self.backendUrl + '/api/version')
        data = await response.json()
        self.urls = data['api']['urls']
        logger.debug('Found ' + str(len(self.urls)) + ' urls')

    def set_octo_id(self, octo_id, api_key):
        self.octo_id = octo_id
        self.api_key = api_key
        for key, value in self.urls.items():
            self.urls[key] = value.replace(':uuid', str(self.octo_id))

    def connect_wss(self, on_message, on_open=None, on_close=None, on_error=None):
        self._ws = WebSocketClient(self.backend_ws_url,
                                   self.octo_id,
                                   self.api_key,
                                   on_message,
                                   on_open=on_open,
                                   on_error=on_error,
                                   on_close=on_close)
        logger.debug('Connecting to ' + self.backend_ws_url)
        self._ws.connect()
        return self._ws
