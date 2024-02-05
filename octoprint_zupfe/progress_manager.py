import time

from octoprint_zupfe.polling_thread import PollingThread


class ProgressThread(PollingThread):
    def __init__(self, plugin):
        super().__init__(stop_if_no_recipients=True)
        self._plugin = plugin

    def poll(self):
        p2p = self._plugin.p2p
        progress = self._plugin.progress
        while True:
            try:
                message = p2p.post_progress(progress.get_progress())
                self.send_frame(message['buffer'])

                time.sleep(0.2)  # send progress in short periods so ui has no hiccups
            except Exception as e:
                self._plugin.logger.debug('Error while taking or sending temperature ' + str(e))
                time.sleep(2)


class ProgressManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._thread = None

    def add_recipient(self, transport):
        if self._thread is None:
            self._plugin.logger.debug('Starting progress thread')
            self._thread = ProgressThread(self._plugin)
            self._thread.start()

        self._thread.add_transport(transport)

    def remove_recipient(self, transport):
        self._thread.remove_transport(transport)
        if not self._thread.has_recipients:
            self._plugin.logger.debug('No more recipients in progress thread, stopping it')
            self._thread.stop()
            self._thread = None

