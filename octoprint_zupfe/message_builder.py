import uuid
import time

from octoprint_zupfe.constants import MESSAGE_EMPTY, MESSAGE_JSON, MESSAGE_STRING, MESSAGE_BINARY, MESSAGE_REPLY, \
    MESSAGE_EVENT, MESSAGE_COMMAND, MESSAGE_STREAM, MESSAGE_REJECT
from octoprint_zupfe.message_coder import MessageCoderV1, encode_json, encode_string
from octoprint_zupfe.message_wrapper import MessageWrapper


def create_info(data_type, details=None, id=None):
    details = details if details else {}
    return {
        'id': id if id else str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'dataType': data_type,
        'details': details
    }


class MessageBuilder:
    def __init__(self, coder=None):
        self._coder = coder if coder else MessageCoderV1()

    # -------------------------------------------------------------------------

    def new_message(self, type, details, content=None):
        info = create_info(type, details)
        buffer = self._coder.pack(info, content)
        return {
            'info': info,
            'buffer': buffer
        }

    def new_empty(self, details=None):
        return self.new_message(MESSAGE_EMPTY, details or {})

    def new_json(self, content, details=None):
        return self.new_message(MESSAGE_JSON, details or {}, encode_json(content))

    def new_string(self, content, details=None):
        return self.new_message(MESSAGE_STRING, details or {}, encode_string(content))

    def new_binary(self, content, details=None):
        return self.new_message(MESSAGE_BINARY, details or {}, content)

    # -------------------------------------------------------------------------

    def new_variant(self, type, details, data):
        details = {'type': type, **details}
        if isinstance(data, bytearray):  # Assuming bytearray for binary data
            return self.new_binary(data, details)
        elif isinstance(data, dict) or isinstance(data, list):  # Handle dict or list as JSON
            return self.new_json(data, details)
        elif isinstance(data, str):
            return self.new_string(data, details)
        else:
            return self.new_empty(details)

    # -------------------------------------------------------------------------

    def new_reply(self, message, data):
        reply_to = message.info['id']
        return self.new_variant(MESSAGE_REPLY, {'replyTo': reply_to}, data)

    def new_rejection(self, message, error):
        reply_to = message.info.id
        return self.new_variant(MESSAGE_REJECT, {'replyTo': reply_to}, error)

    def new_event(self, event, data):
        return self.new_variant(MESSAGE_EVENT, {'event': event}, data)

    def new_command(self, command, data):
        return self.new_variant(MESSAGE_COMMAND, {'command': command}, data)

    def new_stream_chunk(self, stream_id, data):
        details = {'type': MESSAGE_STREAM, 'streamId': stream_id}
        return self.new_binary(data, details)

    def new_stream_end(self, stream_id):
        details = {'type': MESSAGE_STREAM, 'streamId': stream_id}
        return self.new_empty(details)

    # -------------------------------------------------------------------------

    def unpack(self, buffer):
        # Assuming MessageWrapper is a separate class you need to define
        # This is a placeholder for actual implementation
        return MessageWrapper(self._coder.unpack(buffer))
