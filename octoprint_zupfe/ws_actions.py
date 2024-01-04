from octoprint_zupfe.constants import EVENT_PRINTER_PROGRESS


class P2PActions:
    def __init__(self, plugin):
        self._plugin = plugin

    async def post_progress(self, progress):
        builder = self._plugin.message_builder
        transport = self._plugin.transport
        if builder is not None and transport is not None:
            data = {
                'uuid': self._plugin.backend.octo_id,
                'progress': progress
            }
            message = builder.new_event(EVENT_PRINTER_PROGRESS, data)
            transport.send_binary(message['buffer'])
