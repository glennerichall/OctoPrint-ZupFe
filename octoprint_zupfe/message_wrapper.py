from datetime import datetime

from .constants import MESSAGE_JSON, MESSAGE_EMPTY, MESSAGE_BINARY, MESSAGE_STRING, MESSAGE_EVENT, \
    MESSAGE_COMMAND, MESSAGE_STREAM, MESSAGE_REPLY, MESSAGE_MJPEG
from .message_coder import decode_json, decode_string


class MessageWrapper:
    def __init__(self, message):
        self._message = message
        self._info = message['info']
        self._data = message['data']
        self._version = message['version']

    @property
    def info(self):
        return self._info

    @property
    def version(self):
        return self._version

    @property
    def data_type(self):
        return self._info['dataType']

    @property
    def type(self):
        return self.info['messageType']

    @property
    def datetime(self):
        # Assuming timestamp is in milliseconds
        return datetime.datetime.fromtimestamp(self.timestamp / 1000)

    @property
    def timestamp(self):
        return self.info['timestamp']

    @property
    def is_json(self):
        return self.data_type == MESSAGE_JSON

    @property
    def is_empty(self):
        return self.data_type == MESSAGE_EMPTY

    @property
    def is_binary(self):
        return self.data_type == MESSAGE_BINARY

    @property
    def is_string(self):
        return self.data_type == MESSAGE_STRING

    @property
    def is_event(self):
        return self.type == MESSAGE_EVENT

    @property
    def is_command(self):
        return self.type == MESSAGE_COMMAND

    @property
    def is_stream(self):
        return self.type == MESSAGE_STREAM

    @property
    def is_mjpeg(self):
        return self.type == MESSAGE_MJPEG

    @property
    def is_reply(self):
        return self.type == MESSAGE_REPLY

    @property
    def buffer(self):
        return self._data

    @property
    def event(self):
        return self.info['messageMeta']

    @property
    def command(self):
        return self.info['messageMeta']

    @property
    def replies_to(self):
        return self.info['messageMeta']

    @property
    def stream_id(self):
        return self.info['messageMeta']

    def json(self):
        return decode_json(self._data)

    def string(self):
        return decode_string(self._data)

    def u_int8_array(self):
        return bytearray(self._data)

    def array(self):
        return list(self._data)

    def get_data(self):
        if self.is_json:
            return self.json()
        elif self.is_binary:
            return self.buffer
        elif self.is_string:
            return self.string()
        return None
