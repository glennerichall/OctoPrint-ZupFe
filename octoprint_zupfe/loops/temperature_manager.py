from octoprint_zupfe.loops.polling_thread import PollingThreadWithInterval


class TemperatureThread(PollingThreadWithInterval):
    def __init__(self, plugin):
        super().__init__(stop_if_no_recipients=False, interval=1)
        self._plugin = plugin
        self._printer = self._plugin.printer
        self._p2p = self._plugin.p2p
        self._progress = self._plugin.progress

    def poll_message(self):
        temperatures = self._printer.get_current_temperatures()

        # FIXME not supposed to be here
        self._progress.updateTemperatures(temperatures)

        message = self._p2p.post_temperatures(temperatures)
        return message

    def on_polling_error(self, e):
        self._plugin.logger.debug('Error while taking or sending temperature ' + str(e))


class TemperatureManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._thread = TemperatureThread(self._plugin)
        self._thread.start()

    def add_recipient(self, transport, interval=1):
        self._thread.add_transport(transport, interval)

    def remove_recipient(self, transport):
        self._thread.remove_transport(transport)
