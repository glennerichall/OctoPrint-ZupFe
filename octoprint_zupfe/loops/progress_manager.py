from octoprint_zupfe.loops.polling_thread import PollingThreadWithInterval


class ProgressThread(PollingThreadWithInterval):
    def __init__(self, plugin):
        super().__init__(stop_if_no_recipients=True, interval=0.1)
        self._plugin = plugin
        self._p2p = self._plugin.p2p
        self._progress = self._plugin.progress

    def poll_message(self):
        progress = self._progress.get_progress()
        return self._p2p.post_progress(progress)

    def on_polling_error(self, e):
        self._plugin.logger.debug('Error while taking or sending printing progress ' + str(e))


class ProgressManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._thread = None

    def add_recipient(self, transport, interval=10):
        if self._thread is None:
            self._plugin.logger.debug('Starting Progress thread')
            self._thread = ProgressThread(self._plugin)
            self._thread.start()
        return self._thread.add_transport(transport, interval)

    def remove_recipient(self, transport, is_fast=False):
        result = False
        if self._thread is not None:
            result = self._thread.remove_transport(transport)
            if not self._thread.has_recipients:
                self._plugin.logger.debug('No more recipients in Progress thread, stopping it')
                self._thread.stop()
                self._thread = None
        return result
