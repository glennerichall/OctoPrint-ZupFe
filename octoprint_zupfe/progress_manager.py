import time

from octoprint_zupfe.polling_thread import PollingThread


class ProgressThread(PollingThread):
    def __init__(self, plugin, interval=0.1):
        super().__init__(stop_if_no_recipients=True)
        self._plugin = plugin
        self._interval = interval

    def poll(self):
        p2p = self._plugin.p2p
        progress = self._plugin.progress
        while True:
            try:
                message = p2p.post_progress(progress.get_progress())
                self.send_frame(message['buffer'])

                time.sleep(self._interval)  # for fast send progress in short periods so ui has no hiccups
            except Exception as e:
                self._plugin.logger.debug('Error while taking or sending printing progress ' + str(e))
                time.sleep(2)


class ProgressManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._slow_thread = None
        self._fast_thread = None

    def add_recipient(self, transport, is_fast=False):
        if is_fast:
            if self._fast_thread is None:
                self._plugin.logger.debug('Starting Fast Progress thread')
                self._fast_thread = ProgressThread(self._plugin, 0.1)
                self._fast_thread.start()
            return self._fast_thread.add_transport(transport)
        else:
            if self._slow_thread is None:
                self._plugin.logger.debug('Starting Slow Progress thread')
                self._slow_thread = ProgressThread(self._plugin)
                self._slow_thread.start()
            return self._slow_thread.add_transport(transport)

    def remove_recipient(self, transport, is_fast=False):
        result = False
        if is_fast:
            if self._fast_thread is not None:
                result = self._fast_thread.remove_transport(transport)
                if not self._fast_thread.has_recipients:
                    self._plugin.logger.debug('No more recipients in Fast Progress thread, stopping it')
                    self._fast_thread.stop()
                    self._fast_thread = None
        else:
            if self._slow_thread is not None:
                result = self._slow_thread.remove_transport(transport)
                if not self._slow_thread.has_recipients:
                    self._plugin.logger.debug('No more recipients in Slow Progress thread, stopping it')
                    self._slow_thread.stop()
                    self._slow_thread = None
        return result

