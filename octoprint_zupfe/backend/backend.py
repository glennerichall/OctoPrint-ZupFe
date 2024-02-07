import logging

from octoprint_zupfe.transport.request import request_get, request
from octoprint_zupfe.transport.websocket import WebSocketClient

logger = logging.getLogger("octoprint.plugins.zupfe")


class Backend:
    def __init__(self, backend_url, frontend_url):
        self._octo_id = None
        self._api_key = None
        self._original_urls = None
        self._urls_with_id = None
        self._ws = None
        self._backend_url = backend_url
        self._frontend_url = frontend_url

        # FIXME hardcoded url
        self._backend_ws_url = backend_url.replace('https://', 'wss://') + '/api/v1/printers'

    @property
    def backend_url(self):
        return self._backend_url

    @property
    def octo_id(self):
        return self._octo_id

    @property
    def urls(self):
        return self._urls_with_id if self._urls_with_id is not None else self._original_urls

    @property
    def api_key(self):
        return self._api_key

    @property
    def ws(self):
        return self._ws

    async def request(self, method, url, headers=None, data=None, max_retries=float('inf')):
        if headers is None:
            headers = {}

        if self.api_key is not None:
            headers = {**headers, "x-api-key": self.api_key}

        return await request(method, url, headers=headers, data=data, max_retries=max_retries)

    @property
    def is_initialized(self):
        return self.urls is not None and self.octo_id is not None

    @property
    def is_connected(self):
        return self._ws is not None and self._ws.is_connected

    async def init(self):
        logger.debug('Fetching api urls')
        response = await request_get(self.backend_url + '/api/version')
        data = await response.json()
        self._original_urls = data['api']['urls']
        logger.debug('Found ' + str(len(self._original_urls)) + ' urls')

    def set_octo_id(self, octo_id, api_key):
        self._octo_id = octo_id
        self._api_key = api_key
        self._urls_with_id = {}
        for key, value in self._original_urls.items():
            self._urls_with_id[key] = value.replace(':uuid', str(self.octo_id))

    def connect_wss(self, on_message, on_open=None, on_close=None, on_error=None):
        self._ws = WebSocketClient(self._backend_ws_url,
                                   self.octo_id,
                                   self.api_key,
                                   on_message,
                                   on_open=on_open,
                                   on_error=on_error,
                                   on_close=on_close)
        logger.debug('Connecting to ' + self._backend_ws_url)
        self._ws.connect()
        return self._ws

