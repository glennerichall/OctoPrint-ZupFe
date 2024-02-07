import json
import struct


def encode_json(content):
    data = json.dumps(content)
    return data.encode('utf-8')


def encode_string(content):
    return content.encode('utf-8')


def decode_string(content):
    return content.decode('utf-8')


def decode_json(content):
    data = content.decode('utf-8')
    return json.loads(data)


class MessageCoderV1:
    def __init__(self):
        self.version = 1

    def pack(self, info, content=None):
        header_length = 27

        if content is not None:
            content_length = len(content)
            format_str = f'>BIQQBHQ{content_length}s'
            packed_data = struct.pack(format_str,
                                      self.version,
                                      header_length,
                                      info['id'],
                                      info['timestamp'],
                                      info['dataType'],
                                      info['messageType'],
                                      info['messageMeta'],
                                      content)
        else:
            format_str = f'>BIQQBHQ'
            packed_data = struct.pack(format_str,
                                      self.version,
                                      header_length,
                                      info['id'],
                                      info['timestamp'],
                                      info['dataType'],
                                      info['messageType'],
                                      info['messageMeta'], )

        return packed_data

    def unpack(self, buffer):
        unpacked_data = struct.unpack_from('>BIQQBHQ', buffer, 0)

        version = unpacked_data[0]
        header_length = unpacked_data[1]
        info_id = unpacked_data[2]
        timestamp = unpacked_data[3]
        data_type = unpacked_data[4]
        message_type = unpacked_data[5]
        message_meta = unpacked_data[6]

        if version != self.version:
            raise ValueError(f"Bad message version {version} != {self.version}")

        header_end = 5 + header_length
        content = buffer[header_end:]

        return {
            'version': version,
            'info': {
                'id': info_id,
                'timestamp': timestamp,
                'dataType': data_type,
                'messageType': message_type,
                'messageMeta': message_meta
            },
            'data': content
        }
