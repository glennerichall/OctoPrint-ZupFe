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
        header = encode_json(info)

        if content is not None:
            content_length = len(content)
            format_str = f'>BI{len(header)}s{content_length}s'
            packed_data = struct.pack(format_str, self.version, len(header), header, content)
        else:
            format_str = f'>BI{len(header)}s'
            packed_data = struct.pack(format_str, self.version, len(header), header)

        return packed_data

    def unpack(self, buffer):
        version, header_size = struct.unpack_from('>BI', buffer, 0)
        if version != self.version:
            raise ValueError(f"Bad message version {version} != {self.version}")
        header_end = 5 + header_size
        header = buffer[5:header_end]
        content = buffer[header_end:]
        info = decode_json(header)
        return {
            'version': version,
            'info': info,
            'data': content
        }
