import logging
import random
import threading

import requests

from .message_builder import MessageBuilder, max_safe_integer_js

logger = logging.getLogger("octoprint.plugins.zupfe")


class MjpegCameraThread:
    def __init__(self, webcam):
        self._webcam = webcam
        self._transports = {}
        self._thread = None

    def add_transport(self, transport):
        uuid = transport.uuid

        if uuid is not None and uuid not in self._transports:
            remove_callback = transport.on_close(lambda _transport:
                                                 self.remove_transport(transport))
            self._transports[uuid] = {
                'transport': transport,
                'remove_callback': remove_callback
            }
            return True

        return False

    def remove_transport(self, transport):
        uuid = transport.uuid
        if uuid in self._transports:
            transport_info = self._transports.pop(uuid)
            transport_info['remove_callback']()
            return True
        return False

    def send_frame(self, frame):
        for uuid, transport_info in self._transports.items():
            try:
                transport = transport_info['transport']
                transport.send_binary(frame)
            except Exception as e:
                pass

    def read_stream(self):
        mjpeg_url = self._webcam.stream_url
        stream_id = self._webcam.id

        try:
            resp = requests.get(mjpeg_url, stream=True)
            stream = b''
            builder = MessageBuilder()

            for chunk in resp.iter_content(chunk_size=1024):
                stream += chunk
                # Check if the buffer contains the start and end of a frame
                start = stream.find(b'\xff\xd8')
                end = stream.find(b'\xff\xd9', start)

                # when mjpeg frame is found send it to server through websocket or send it to client
                # through webrtc data channel
                if start != -1 and end != -1:
                    end = end + 2
                    frame = stream[start:end]
                    stream = stream[end:]
                    message = builder.new_mjpeg_frame(frame, stream_id)

                    self.send_frame(message['buffer'])

        except Exception as e:
            logger.debug("Unable to read stream from %s: %s" % (mjpeg_url, e))

    def start(self):
        thread = threading.Thread(target=self.read_stream)
        self._thread = thread

        # daemon mode is mandatory so threads get killed when server shuts down
        thread.daemon = True
        thread.start()


class MjpegStreamManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._threads = {}

    def start_camera(self, camera_id, transport):
        webcam_to_stream = None
        for webcam in self._plugin.stream_webcams:
            if webcam.id == camera_id:
                webcam_to_stream = webcam

        if webcam_to_stream is not None:
            if not camera_id in self._threads:
                self._threads[camera_id] = MjpegCameraThread(webcam_to_stream)
                self._threads[camera_id].start()

            return self._threads[camera_id].add_transport(transport)

        return False

    def stop_camera(self, camera_id, transport):
        if not camera_id in self._threads:
            return False
        else:
            self._threads[camera_id].remove_transport(transport)
            return True
