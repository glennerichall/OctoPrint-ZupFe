import logging
import time
from .constants import URL_PRINTER_TITLE, \
    URL_PRINTER_STATUS, EVENT_REQUEST_STREAM, \
    URL_PRINTER_EVENT, URL_PRINTER_LINK, \
    URL_PRINTERS, URL_PRINTER_SNAPSHOT
import websocket
import ssl
import threading
import json
from urllib.parse import urlencode

from .request import request_get_json, request_post_json, request_put, create_reply, create_stream, request_post, \
    request_delete, create_rejection

logger = logging.getLogger("octoprint.plugins.zupfe.backend")


class WebSocketClient:
    def __init__(self, backend_ws_url, octo_id, api_key, on_message,
                 on_open=None, on_close=None, on_error=None):
        headers = {
            'x-printer-uuid': octo_id,
            'x-api-key': api_key
        }
        # Create a custom SSL context that allows self-signed certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        # websocket.enableTrace(True)

        self._thread = threading.Thread(target=self._run_forever)

        self._connected = False
        self._connection_future = None
        self._closed = True

        self._on_open_callback = on_open
        self._on_message_callback = on_message
        self._on_close_callback = on_close
        self._on_error_callback = on_error

        self._ws = websocket.WebSocketApp(backend_ws_url,
                                          header=headers,
                                          on_open=self._on_open,
                                          on_message=self._on_message,
                                          on_error=self._on_error,
                                          on_close=self._on_close)

    def is_connected(self):
        return self._connected

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info('Websocket closed')
        self._connected = False
        if self._on_close_callback is not None:
            self._on_close_callback()

    def _on_error(self, ws, error_message):
        logger.error(f"Websocket closed: {error_message}")
        self._connected = False
        ws.close()
        if self._on_error_callback is not None:
            self._on_error_callback()

    def _on_message(self, ws, message):
        # print(f"Received message from server: {message}")
        message = json.loads(message.decode('utf-8'))
        if message['cmd'] == EVENT_REQUEST_STREAM:
            reply = create_stream(ws, message)
        else:
            reply = create_reply(ws, message)

        reject = create_rejection(ws, message)
        self._on_message_callback(message, reply=reply, reject=reject)

    def _on_open(self, wssapp):
        logger.info('Websocket opened')
        self._connected = True
        if self._on_open_callback is not None:
            self._on_open_callback()

    def _run_forever(self, retry_interval=1):
        while not self._closed:
            try:
                self._ws.run_forever(skip_utf8_validation=True, sslopt={"cert_reqs": ssl.CERT_NONE})
                if self._connected:
                    self._ws.close()
                    self._on_close(None, None, None)

                self._connected = False
                time.sleep(retry_interval)
            except websocket.WebSocketException as e:
                pass

    def close(self):
        self._closed = True

    def connect(self):
        self._closed = False
        self._thread.start()


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

    def is_initialized(self):
        return self.urls is not None and self.octo_id is not None

    def is_connected(self):
        return self._ws is not None and self._ws.is_connected()

    async def init(self):
        logger.debug('Fetching api urls')
        data = await request_get_json(self.backendUrl + '/api/version')
        self.urls = data['api']['urls']
        logger.debug('Found ' + str(len(self.urls)) + ' urls')

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

    async def new_octo_id(self):
        instance = await request_post_json(self.urls[URL_PRINTERS])
        octo_id = instance['uuid']
        api_key = instance['apiKey']
        self.set_octo_id(octo_id, api_key)
        return instance

    async def post_snapshot(self, config, snapshot):
        post_url = self.urls[URL_PRINTER_SNAPSHOT]
        headers = {"x-api-key": self.api_key}
        post_url = post_url + "?" + urlencode(config)
        post_info = await request_post_json(post_url, headers=headers)
        await request_put(post_info['uploadURL'], None, headers=headers, data=snapshot)

    async def post_event(self, event):
        headers = {"X-Api-Key": self.api_key}
        url = self.urls[URL_PRINTER_EVENT].replace(':event', event)
        await request_post(url, None, headers=headers)

    def set_octo_id(self, octo_id, api_key):
        self.octo_id = octo_id
        self.api_key = api_key
        for key, value in self.urls.items():
            self.urls[key] = value.replace(':uuid', str(self.octo_id))

    async def set_printer_title(self, title, max_retries=1):
        data = {'title': title}
        headers = {"X-Api-Key": self.api_key}
        await request_post_json(self.urls[URL_PRINTER_TITLE], headers=headers, data=data, max_retries=max_retries)

    async def get_link_status(self):
        headers = {"X-Api-Key": self.api_key}
        return await request_get_json(self.urls[URL_PRINTER_STATUS], headers=headers)

    async def unlink(self):
        headers = {"X-Api-Key": self.api_key}
        return await request_delete(self.urls[URL_PRINTER_LINK], None, headers=headers)
