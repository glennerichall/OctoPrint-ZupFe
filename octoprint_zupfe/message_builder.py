import random
import uuid
import time

from octoprint_zupfe.constants import MESSAGE_EMPTY, MESSAGE_JSON, MESSAGE_STRING, MESSAGE_BINARY, MESSAGE_REPLY, \
    MESSAGE_EVENT, MESSAGE_COMMAND, MESSAGE_STREAM, MESSAGE_REJECT
from octoprint_zupfe.message_coder import MessageCoderV1, encode_json, encode_string
from octoprint_zupfe.message_wrapper import MessageWrapper

# JavaScript's MAX_SAFE_INTEGER is 2^53 - 1
max_safe_integer_js = 2 ** 53 - 1


def create_info(data_type, message_type, message_meta, id=None):
    return {
        'id': id if id else random.randint(0, max_safe_integer_js - 1),
        'timestamp': int(time.time() * 1000),
        'dataType': data_type,
        'messageType': message_type,
        'messageMeta': message_meta,
    }


class MessageBuilder:
    def __init__(self, coder=None):
        self._coder = coder if coder else MessageCoderV1()

    # -------------------------------------------------------------------------

    def new_message(self, data_type, message_type, message_meta, content=None):
        info = create_info(data_type, message_type, message_meta)
        buffer = self._coder.pack(info, content)
        return {
            'info': info,
            'buffer': buffer
        }

    def new_empty(self, message_type=0, message_meta=0):
        return self.new_message(MESSAGE_EMPTY, message_type, message_meta)

    def new_json(self, content, message_type=0, message_meta=0):
        return self.new_message(MESSAGE_JSON, message_type, message_meta, encode_json(content))

    def new_string(self, content, message_type=0, message_meta=0):
        return self.new_message(MESSAGE_STRING, message_type, message_meta, encode_string(content))

    def new_binary(self, content, message_type=0, message_meta=0):
        return self.new_message(MESSAGE_BINARY, message_type, message_meta, content)

    # -------------------------------------------------------------------------

    def new_variant(self, message_type, message_meta, data):
        if isinstance(data, bytearray):  # Assuming bytearray for binary data
            return self.new_binary(data, message_type, message_meta)
        elif isinstance(data, dict) or isinstance(data, list):  # Handle dict or list as JSON
            return self.new_json(data, message_type, message_meta)
        elif isinstance(data, str):
            return self.new_string(data, message_type, message_meta)
        else:
            return self.new_empty(message_type, message_meta)

    # -------------------------------------------------------------------------

    def new_reply(self, message, data):
        reply_to = message.info['id']
        return self.new_variant(MESSAGE_REPLY, reply_to, data)

    def new_rejection(self, message, error):
        reply_to = message.info.id
        return self.new_variant(MESSAGE_REJECT, reply_to, error)

    def new_event(self, event, data):
        return self.new_variant(MESSAGE_EVENT,  event, data)

    def new_command(self, command, data):
        return self.new_variant(MESSAGE_COMMAND,  command, data)

    def new_stream_chunk(self, stream_id, data):
        return self.new_binary(data, MESSAGE_STREAM, stream_id)

    def new_stream_end(self, stream_id):
        return self.new_empty(MESSAGE_STREAM, stream_id)

    # -------------------------------------------------------------------------

    def unpack(self, buffer):
        # Assuming MessageWrapper is a separate class you need to define
        # This is a placeholder for actual implementation
        return MessageWrapper(self._coder.unpack(buffer))
