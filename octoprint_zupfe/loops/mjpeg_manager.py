from octoprint_zupfe.loops.polling_manager import PollingManager
from octoprint_zupfe.messaging.message_builder import MessageBuilder
from octoprint_zupfe.loops.polling_thread import PollingThread


class MjpegCameraThread(PollingThread):
    def __init__(self, webcam, plugin):
        super().__init__("mjpeg", stop_if_no_recipients=True)
        self._plugin = plugin
        self._webcam = webcam

    def poll(self):
        self.on_polling_started()
        stream_id = self._webcam.id
        builder = MessageBuilder()

        def receive_frame(frame):
            message = builder.new_mjpeg_frame(frame, stream_id)
            self.send_frame(message['buffer'])

        def is_done():
            return self._done

        self._webcam.read_mjpeg_frames(receive_frame, is_done)

        self.on_polling_done()


class MjpegManager(PollingManager):
    def __init__(self, plugin, webcam):
        super().__init__(plugin, "MJPEG", 1)
        self._webcam = webcam

    def create_thread(self, plugin):
        return MjpegCameraThread(self._webcam, self._plugin)


class MjpegStreamManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._managers = {}

    def add_recipient(self, transport, interval, camera_id = None):
        webcam_to_stream = None
        for webcam in self._plugin.stream_webcams:
            if webcam.id == camera_id:
                webcam_to_stream = webcam

        if webcam_to_stream is not None:
            if not camera_id in self._managers:
                self._managers[camera_id] = MjpegManager(self._plugin, webcam_to_stream)

            manager = self._managers[camera_id]

            if not manager.running:
                self._managers[camera_id].start()

            manager.add_recipient(transport, interval)

        return True


    def remove_recipient(self, transport, camera_id):
        if not camera_id in self._managers:
            return False
        else:
            manager = self._managers[camera_id]
            self._plugin.logger.debug(f"Unregistering transport {transport.uuid} ({transport.type}) from camera {camera_id}")

            manager.remove_recipient(transport)

            if manager.is_done:
                self._plugin.logger.debug(f"Camera {camera_id} has no more recipients, stopping thread")
                self._managers.pop(camera_id)

            return True
