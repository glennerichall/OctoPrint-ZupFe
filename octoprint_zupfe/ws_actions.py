from octoprint_zupfe.constants import EVENT_PRINTER_PROGRESS, EVENT_PRINTER_TEMPERATURE


class P2PActions:
    def __init__(self, plugin):
        self._plugin = plugin

    async def post_progress(self, progress):
        builder = self._plugin.message_builder
        data = {
            'uuid': self._plugin.backend.octo_id,
            'progress': progress
        }
        message = builder.new_event(EVENT_PRINTER_PROGRESS, data)
        return message
            # transport.send_binary(message['buffer'])

    async def post_temperatures(self, temperatures):
        builder = self._plugin.message_builder
        data = {
            'uuid': self._plugin.backend.octo_id,
            'temperatures': temperatures
        }
        message = builder.new_event(EVENT_PRINTER_TEMPERATURE, data)
        return message

        # transport.send_binary(message['buffer'])
