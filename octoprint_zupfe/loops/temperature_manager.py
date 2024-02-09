from octoprint_zupfe.loops.polling_manager import PollingManager
from octoprint_zupfe.loops.polling_thread import PollingThreadWithInterval


class TemperatureThread(PollingThreadWithInterval):
    def __init__(self, plugin):
        super().__init__("Temperature", stop_if_no_recipients=False, interval=1)
        self._plugin = plugin
        self._printer = self._plugin.printer
        self._message_factory = self._plugin.message_factory
        self._progress = self._plugin.progress

    def poll_message(self):
        temperatures = self._printer.get_current_temperatures()

        # FIXME not supposed to be here
        self._progress.updateTemperatures(temperatures)

        message = self._message_factory.post_temperatures(temperatures)
        return message

    def on_polling_error(self, e):
        # pass
        self._plugin.logger.debug('Error while taking or sending temperature: ' + str(e))


class TemperatureManager(PollingManager):
    def __init__(self, plugin):
        super().__init__(plugin, "Temperature", 1)

    def create_thread(self, plugin):
        return TemperatureThread(plugin)


