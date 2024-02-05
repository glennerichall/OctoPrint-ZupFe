import json
import logging
import ssl
import threading
import time
import uuid

import websocket

from octoprint_zupfe.constants import RPC_REQUEST_STREAM
from octoprint_zupfe.message_builder import MessageBuilder
from octoprint_zupfe.request import create_stream, create_reply, create_rejection

logger = logging.getLogger("octoprint.plugins.zupfe")


class WebSocketTransport:
    def __init__(self, ws, ws_id):
        self._ws = ws
        self._ws_id = ws_id

    @property
    def uuid(self):
        return self._ws_id

    def send(self, message):
        self._ws.send(message)

    def on_close(self, callback):
        return self._ws.on_close(callback)

    def send_binary(self, message):
        self._ws.send_binary(message)


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

        self._close_callbacks = []
        self._thread = threading.Thread(target=self._run_forever)

        self._connected = False
        self._connection_future = None
        self._closed = True

        self._on_open_callback = on_open
        self._on_message_callback = on_message
        self._on_close_callback = on_close
        self._on_error_callback = on_error

        self._uuid = str(uuid.uuid4())

        self._ws = websocket.WebSocketApp(backend_ws_url,
                                          header=headers,
                                          on_open=self._on_open,
                                          on_message=self._on_message,
                                          on_error=self._on_error,
                                          on_close=self._on_close)

    @property
    def uuid(self):
        return self._uuid

    @property
    def is_connected(self):
        return self._connected

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info('Websocket closed')
        self._connected = False
        if self._on_close_callback is not None:
            self._on_close_callback()

        for callback in self._close_callbacks:
            callback(self)

    def _on_error(self, ws, error_message):
        logger.error(f"Websocket closed: {error_message}")
        self._connected = False
        ws.close()
        if self._on_error_callback is not None:
            self._on_error_callback()

    def send(self, message):
        self._ws.send(message)

    def send_binary(self, message):
        self._ws.send(message, websocket.ABNF.OPCODE_BINARY)

    def _on_message(self, ws, message):
        # print(f"Received message from server: {message}")
        # message = json.loads(message.decode('utf-8'))

        message = MessageBuilder().unpack(message)

        reject = create_rejection(self, message)
        if not message.is_command and not message.is_event:
            reject()

        else:
            if message.command == RPC_REQUEST_STREAM:
                reply = create_stream(self, message)
            else:
                reply = create_reply(self, message)

            content = None
            if message.is_json:
                content = message.json()

            ws_id = None
            if content is not None and 'wsClientId' in content:
                ws_id = content['wsClientId']

            transport = self
            self._on_message_callback(message, reply=reply, reject=reject, transport=transport)

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

    def on_close(self, callback):
        self._close_callbacks.append(callback)
        return lambda: self._close_callbacks.remove(callback)
