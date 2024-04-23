import asyncio
import logging
import random
import threading
import time
from abc import ABC, abstractmethod

from octoprint_zupfe.messaging.message_builder import max_safe_integer_js

logger = logging.getLogger("octoprint.plugins.zupfe")


def should_evict_transport(name, recipient, error=None):
    transport = recipient['transport']
    if recipient['missed_frames'] > 50:
        logger.debug(
            "Unable to send stream from loop %s to recipient %s more than 100 times consecutively, evicting transport" % (
                name, transport.uuid))
        return True
    return False


class PollingThread(ABC):
    def __init__(self, name, stop_if_no_recipients=True):
        self._recipients = {}
        self._subscriptions = {}
        self._thread = None
        self._done = False
        self._loop = None
        self._epoch = 0
        self._name = name
        self._stop_if_no_recipients = stop_if_no_recipients

    def log_recipients(self):
        logger.debug(f'There are {len(self._recipients)} recipient(s) in the loop of {self._name}')
        message = ''
        for uuid in list(self._recipients.keys()):
            recipient = self._recipients[uuid]
            transport_type = recipient.get('transport').type
            message += f'({transport_type}:{uuid} ) '

        logger.debug(f'Recipient(s) of {self._name} : {message}')

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
            logger.debug(f'Transport {transport.uuid} ({transport.type}) added as a recipient of {self._name}')
        else:
            logger.debug(f'Transport {transport.uuid} ({transport.type}) is already a recipient of {self._name}')

        self.log_recipients()
        return True

    @property
    def is_done(self):
        return self._done

    @property
    def has_recipients(self):
        return len(self._recipients) > 0

    @property
    def running(self):
        return not self._done

    def stop_if_empty(self):
        if not self.has_recipients and self._stop_if_no_recipients:
            logger.debug(
                f'Loop {self._name} has no recipients stopping it')
            self.stop()

    def remove_transport(self, transport):
        uuid = transport.uuid
        if uuid in self._recipients:
            recipient = self._recipients[uuid]
            recipient['remove_callback']()
            self._recipients.pop(uuid)
            logger.debug(f'Transport {transport.uuid} ({transport.type}) removed from {self._name}')
        else:
            logger.debug(f'Transport {transport.uuid} ({transport.type}) not in {self._name}, not removed')

        self.log_recipients()
        self.stop_if_empty()
        return True

    def validate_and_evict_transport(self, name, recipient, error=None):
        if should_evict_transport(name, recipient, error):
            self.remove_transport(recipient['transport'])

    def start(self):
        if self._thread is None:
            self._done = False
            thread = threading.Thread(target=self.poll)
            self._thread = thread

            # daemon mode is mandatory so threads get killed when server shuts down            const client = this.createClient(ws, req);

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
                    self.validate_and_evict_transport(self._name, recipient, e)

    @abstractmethod
    def poll(self):
        pass

    def on_polling_started(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def on_polling_done(self):
        self._loop.close()


class PollingThreadWithInterval(PollingThread):
    def __init__(self, name, stop_if_no_recipients=True, interval=1):
        super().__init__(name, stop_if_no_recipients)
        self._interval = interval

    @abstractmethod
    def poll_message(self):
        pass

    def on_polling_error(self, error):
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
