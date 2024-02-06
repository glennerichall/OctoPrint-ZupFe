import requests

from .message_builder import MessageBuilder
from .polling_thread import PollingThread


class MjpegCameraThread(PollingThread):
    def __init__(self, webcam, plugin):
        super().__init__(stop_if_no_recipients=True)
        self._plugin = plugin
        self._webcam = webcam

    def poll(self):
        stream_id = self._webcam.id
        builder = MessageBuilder()

        def receive_frame(frame):
            message = builder.new_mjpeg_frame(frame, stream_id)
            self.send_frame(message['buffer'])

        def is_done():
            return self._done

        self._webcam.read_mjpeg_frames(receive_frame, is_done)


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
