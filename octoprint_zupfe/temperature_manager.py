import time

from octoprint_zupfe.polling_thread import PollingThread


class TemperatureThread(PollingThread):
    def __init__(self, plugin):
        super().__init__(stop_if_no_recipients=False)
        self._plugin = plugin

    def poll(self):
        printer = self._plugin.printer
        p2p = self._plugin.p2p
        progress = self._plugin.progress
        while True:
            try:
                temperatures = printer.get_current_temperatures()
                progress.updateTemperatures(temperatures)

                message = p2p.post_temperatures(temperatures)
                self.send_frame(message['buffer'])

                time.sleep(1)
            except Exception as e:
                self._plugin.logger.debug('Error while taking or sending temperature ' + str(e))
                time.sleep(2)


class TemperatureManager:
    def __init__(self, plugin):
        self._plugin = plugin
        self._thread = TemperatureThread(self._plugin)
        self._thread.start()

    def add_recipient(self, transport):
        self._thread.add_transport(transport)

    def remove_recipient(self, transport):
        self._thread.remove_transport(transport)
