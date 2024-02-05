import logging
import random
import threading

import requests

from .message_builder import MessageBuilder, max_safe_integer_js
from .polling_thread import PollingThread


class MjpegCameraThread(PollingThread):
    def __init__(self, webcam, plugin):
        super().__init__(stop_if_no_recipients=True)
        self._plugin = plugin
        self._webcam = webcam

    def poll(self):
        mjpeg_url = self._webcam.stream_url
        stream_id = self._webcam.id

        while not self._done:
            try:
                self._plugin.logger.debug("Getting mjpeg stream for camera %s at %s" % (stream_id, mjpeg_url))
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
                self._plugin.logger.debug("Unable to read stream from %s: %s" % (mjpeg_url, e))


class MjpegStreamManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._threads = {}

    def start_camera(self, camera_id, transport):
        webcam_to_stream = None
        for webcam in self._plugin.stream_webcams:
            if webcam.id == camera_id:
                webcam_to_stream = webcam

        self._plugin.logger.debug(f"Registering transport {transport.uuid} to camera {webcam.id}")

        if webcam_to_stream is not None:
            if not camera_id in self._threads or not self._threads[camera_id].running:
                self._threads[camera_id] = MjpegCameraThread(webcam_to_stream, self._plugin)
                self._threads[camera_id].start()

            return self._threads[camera_id].add_transport(transport)

        return False

    def stop_camera(self, camera_id, transport):
        if not camera_id in self._threads:
            return False
        else:
            self._plugin.logger.debug(f"Unregistering transport {transport.uuid} from camera {camera_id}")

            self._threads[camera_id].remove_transport(transport)
            if not self._threads[camera_id].has_recipients:
                self._plugin.logger.debug(f"Camera {camera_id} has no more recipients, stopping thread")
                self._threads[camera_id].stop()
                self._threads.pop(camera_id)
            return True
