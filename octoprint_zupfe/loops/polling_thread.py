import logging
import threading
import time
from abc import ABC, abstractmethod

logger = logging.getLogger("octoprint.plugins.zupfe")


def should_evict_transport(camera_uuid, recipient, error=None):
    transport = recipient['transport']
    if recipient['missed_frames'] > 100:
        logger.debug("Unable to send stream %s to %s more than 100 times consecutively, evicting transport" % (
            camera_uuid, transport.uuid))
        return True
    return False


class PollingThread(ABC):
    def __init__(self, stop_if_no_recipients=True):
        self._recipients = {}
        self._thread = None
        self._done = False
        self._epoch = 0
        self._stop_if_no_recipients = stop_if_no_recipients

    def add_transport(self, transport, interval=1):
        uuid = transport.uuid

        if uuid is not None and uuid not in self._recipients:
            remove_on_close_handler = transport.on_close(lambda _transport: self.remove_transport(_transport))
            self._recipients[uuid] = {
                'interval': interval,
                'transport': transport,
                'remove_callback': remove_on_close_handler,
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
            if not self.has_recipients and self._stop_if_no_recipients:
                self.stop()
            return True
        return False

    def validate_and_evict_transport(self, camera_uuid, recipient, error=None):
        if should_evict_transport(camera_uuid, recipient, error):
            self.remove_transport(recipient['transport'])

    def start(self):
        self._done = False
        thread = threading.Thread(target=self.poll)
        self._thread = thread

        # daemon mode is mandatory so threads get killed when server shuts down
        thread.daemon = True
        thread.start()

    def stop(self):
        self._thread = None
        self._done = True

    def send_frame(self, frame):
        self._epoch = self._epoch + 1
        for uuid in list(self._recipients.keys()):  # Create a copy of keys to iterate over
            recipient = self._recipients[uuid]
            transport = recipient['transport']
            interval = recipient['interval']
            if self._epoch % interval == 0:
                try:
                    transport.send_binary(frame)
                    recipient['missed_frames'] = 0
                except Exception as e:
                    logger.debug("Unable to send stream from %s to %s: %s" % (uuid, transport.uuid, e))
                    recipient['missed_frames'] = recipient['missed_frames'] + 1
                    self.validate_and_evict_transport(uuid, recipient, e)

    @abstractmethod
    def poll(self):
        pass


class PollingThreadWithInterval(PollingThread):
    def __init__(self, stop_if_no_recipients=True, interval=1):
        super().__init__(stop_if_no_recipients)
        self._interval = interval

    def on_polling_started(self):
        pass

    @abstractmethod
    def poll_message(self):
        pass

    def on_polling_error(self, error):
        pass

    def on_polling_done(self):
        pass

    def poll(self):
        self.on_polling_started()
        while not self._done:
            try:
                message = self.poll_message()
                self.send_frame(message['buffer'])
                time.sleep(self._interval)
            except Exception as e:
                self.on_polling_error(e)
                time.sleep(2)

        self.on_polling_done()
