from octoprint_zupfe.constants import EVENT_PRINTER_PROGRESS, EVENT_PRINTER_TEMPERATURE


class MessageFactory:
    def __init__(self, plugin):
        self._plugin = plugin

    def post_progress(self, progress):
        builder = self._plugin.message_builder
        data = {
            'uuid': self._plugin.backend.octo_id,
            'progress': progress
        }
        message = builder.new_event(EVENT_PRINTER_PROGRESS, data)
        return message

    def post_temperatures(self, temperatures):
        builder = self._plugin.message_builder
        data = {
            'uuid': self._plugin.backend.octo_id,
            'temperatures': temperatures
        }
        message = builder.new_event(EVENT_PRINTER_TEMPERATURE, data)
        return message
