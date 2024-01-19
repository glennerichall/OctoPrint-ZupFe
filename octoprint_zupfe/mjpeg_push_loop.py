import random

import requests
import threading

from octoprint_zupfe import MessageBuilder
from octoprint_zupfe.message_builder import max_safe_integer_js


def send_mjpeg_to_websocket(webcam, wsProvider):
    mjpeg_url = webcam.config.extras['stream']

    def read_stream():
        resp = requests.get(mjpeg_url, stream=True)
        stream_id = random.randint(0, max_safe_integer_js - 1)
        stream = b''
        builder = MessageBuilder()
        for chunk in resp.iter_content(chunk_size=1024):
            stream += chunk
            # Check if the buffer contains the start and end of a frame
            start = stream.find(b'\xff\xd8')
            end = stream.find(b'\xff\xd9', start)
            if start != -1 and end != -1:
                end = end + 2
                frame = stream[start:end]
                stream = stream[end:]
                message = builder.new_mjpeg_frame(frame, stream_id)
                ws = wsProvider()
                if ws is not None:
                    try:
                        ws.send_binary(message['buffer'])
                    except Exception as e:
                        pass

    thread = threading.Thread(target=read_stream)
    # daemon mode is mandatory so threads get kill when server shuts down
    thread.daemon = True
    thread.start()
