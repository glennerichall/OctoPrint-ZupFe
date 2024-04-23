from octoprint_zupfe.loops.polling_manager import PollingManager
from octoprint_zupfe.loops.polling_thread import PollingThreadWithInterval


class ProgressThread(PollingThreadWithInterval):
    def __init__(self, plugin):
        super().__init__("progress", stop_if_no_recipients=True, interval=1)
        self._plugin = plugin
        self._p2p = self._plugin.message_factory
        self._progress = self._plugin.progress

    def poll_message(self):
        progress = self._progress.get_progress()
        return self._p2p.post_progress(progress)

    def on_polling_error(self, e):
        self._plugin.logger.debug('Error while taking or sending printing progress ' + str(e))


class ProgressManager(PollingManager):
    def __init__(self, plugin):
       super().__init__(plugin, "Progress", 10)

    def create_thread(self, plugin):
        return ProgressThread(plugin)


