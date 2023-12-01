import requests
import websocket
import threading

from octoprint_zupfe.constants import EVENT_MJPEG_FRAME


def send_mjpeg_to_websocket(mjpeg_url, ws):
    def read_stream():
        resp = requests.get(mjpeg_url, stream=True)

        buffer = b''
        for chunk in resp.iter_content(chunk_size=1024):
            buffer += chunk
            # Check if the buffer contains the start and end of a frame
            if buffer.find(b'\xff\xd8') != -1 and buffer.find(b'\xff\xd9') != -1:
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9', start) + 2
                frame = buffer[start:end]
                buffer = buffer[end:]

                frame = frame + EVENT_MJPEG_FRAME
                ws.send(frame, opcode=websocket.ABNF.OPCODE_BINARY)

        ws.close()

    threading.Thread(target=read_stream).start()
