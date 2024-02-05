import logging
import random
import threading

import requests

from .message_builder import MessageBuilder, max_safe_integer_js

logger = logging.getLogger("octoprint.plugins.zupfe")


def should_evict_transport(camera_uuid, recipient, error=None):
    transport = recipient['transport']
    if recipient['missed_frames'] > 100:
        logger.debug("Unable to send stream %s to %s more than 100 times consecutively, evicting transport" % (
            camera_uuid, transport.uuid))
        return True
    return False


class MjpegCameraThread:
    def __init__(self, webcam):
        self._webcam = webcam
        self._recipients = {}
        self._thread = None
        self._done = False

    def add_transport(self, transport):
        uuid = transport.uuid

        if uuid is not None and uuid not in self._recipients:
            remove_callback = transport.on_close(lambda _transport:
                                                 self.remove_transport(transport))
            self._recipients[uuid] = {
                'transport': transport,
                'remove_callback': remove_callback,
                'missed_frames': 0
            }
            return True

        return False

    @property
    def has_recipients(self):
        return len(self._recipients) > 0

    @property
    def running(self):
        return not self._done

    def remove_transport(self, transport):
        uuid = transport.uuid
        if uuid in self._recipients:
            recipient = self._recipients.pop(uuid)
            recipient['remove_callback']()
            if not self.has_recipients:
                self.stop()
            return True
        return False

    def validate_and_evict_transport(self, camera_uuid, recipient, error=None):
        if should_evict_transport(camera_uuid, recipient, error):
            self.remove_transport(recipient['transport'])

    def send_frame(self, frame):
        for uuid in list(self._recipients.keys()):  # Create a copy of keys to iterate over
            recipient = self._recipients[uuid]
            transport = recipient['transport']
            try:
                transport.send_binary(frame)
                recipient['missed_frames'] = 0
            except Exception as e:
                logger.debug("Unable to send stream from %s to %s: %s" % (uuid, transport.uuid, e))
                recipient['missed_frames'] = recipient['missed_frames'] + 1
                self.validate_and_evict_transport(uuid, recipient, e)

    def read_stream(self):
        mjpeg_url = self._webcam.stream_url
        stream_id = self._webcam.id

        while not self._done:
            try:
                logger.debug("Getting mjpeg stream for camera %s at %s" % (stream_id, mjpeg_url))
                resp = requests.get(mjpeg_url, stream=True)
                stream = b''
                builder = MessageBuilder()

                import time

                # Initialize the start time and frame counter
                start_time = time.time()
                frame_count = 0

                for chunk in resp.iter_content(chunk_size=1024):
                    if self._done:
                        break

                    stream += chunk
                    # Check if the buffer contains the start and end of a frame
                    start = stream.find(b'\xff\xd8')
                    end = stream.find(b'\xff\xd9', start)

                    if start != -1 and end != -1:
                        end = end + 2
                        frame = stream[start:end]
                        stream = stream[end:]
                        message = builder.new_mjpeg_frame(frame, stream_id)

                        # Frame successfully processed, increment frame count
                        frame_count += 1

                        if self._done:
                            break

                        self.send_frame(message['buffer'])

                    # Periodically calculate FPS
                    if time.time() - start_time >= 1:  # Every second
                        fps = frame_count / (time.time() - start_time)
                        print(f"FPS: {fps}")
                        # Reset counters for the next measurement
                        start_time = time.time()
                        frame_count = 0

            except Exception as e:
                logger.debug("Unable to read stream from %s: %s" % (mjpeg_url, e))

    def start(self):
        self._done = False
        thread = threading.Thread(target=self.read_stream)
        self._thread = thread

        # daemon mode is mandatory so threads get killed when server shuts down
        thread.daemon = True
        thread.start()

    def stop(self):
        self._thread = None
        self._done = True


class MjpegStreamManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._threads = {}

    def start_camera(self, camera_id, transport):
        webcam_to_stream = None
        for webcam in self._plugin.stream_webcams:
            if webcam.id == camera_id:
                webcam_to_stream = webcam

        logger.debug(f"Registering transport {transport.uuid} to camera {webcam.id}")

        if webcam_to_stream is not None:
            if not camera_id in self._threads or not self._threads[camera_id].running:
                self._threads[camera_id] = MjpegCameraThread(webcam_to_stream)
                self._threads[camera_id].start()

            return self._threads[camera_id].add_transport(transport)

        return False

    def stop_camera(self, camera_id, transport):
        if not camera_id in self._threads:
            return False
        else:
            logger.debug(f"Unregistering transport {transport.uuid} from camera {camera_id}")

            self._threads[camera_id].remove_transport(transport)
            if not self._threads[camera_id].has_recipients:
                logger.debug(f"Camera {camera_id} has no more recipients, stopping thread")
                self._threads[camera_id].stop()
                self._threads.pop(camera_id)
            return True
