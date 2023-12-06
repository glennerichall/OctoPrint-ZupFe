import asyncio

from . import take_snapshots_daily, handle_message
from .backend_sync import update_title_if_changed
from .power_state_poll_loop import start_power_state_poll_loop, start_progress_push_loop


def start_poll_loops(plugin):
    plugin.worker.run_thread_safe(
        start_power_state_poll_loop(plugin.printer,
                                    plugin.actions))

    while not plugin.backend.is_initialized:
        asyncio.sleep(2)  # wait 2 seconds before checking if backend has received its urls

    plugin.worker.run_thread_safe(
        start_progress_push_loop(plugin.progress,
                                 plugin.p2p))

    plugin.worker.run_thread_safe(
        take_snapshots_daily(plugin.webcam, plugin.actions))


def initialize_backend_async(plugin):

    async def on_connected():
        plugin.logger.debug("Connected to websocket")
        try:
            await update_title_if_changed(plugin)
            plugin.frontend.emitBackendConnected()
        except Exception as e:
            plugin.logger.error(str(e))

    async def initialize_backend():
        await plugin.backend.init()
        plugin.frontend.emitInitialized()

        octo_id = plugin.settings.get('octoprint_id', None)
        api_key = plugin.settings.get('api_key', None)

        uuid_valid = False
        while not uuid_valid:
            if octo_id is None:
                plugin.logger.debug('No octoid, asking for a new one')
                instance = await plugin.actions.new_octo_id()
                octo_id = instance['uuid']
                api_key = instance['apiKey']
                plugin.logger.debug('Got a new octoid')
                plugin.settings.save_if_updated('octoprint_id', octo_id)
                plugin.settings.save_if_updated('api_key', api_key)
                plugin.settings.save_if_updated('linked', False)
            else:
                plugin.backend.set_octo_id(octo_id, api_key)

            uuid_valid = await plugin.actions.check_uuid()

            if not uuid_valid:
                plugin.logger.debug('Octoid not found on backend or api key is invalid, flushing octoid')
                octo_id = None
                api_key = None

        # must transmit api key because:
        # jinja may not have access to value when rendering wizard
        # self.settings.settings.plugins.zupfe.api_key in zupfe.js does not seem to get settings everytime
        plugin.frontend.emitApiKey(api_key)

        try:
            await update_title_if_changed(plugin)

            plugin.logger.debug('Connecting to websocket')
            plugin.backend.connect_wss(on_message=lambda message, reply, reject: handle_message(plugin, message, reply, reject),
                                       on_close=plugin.frontend.emitBackendDisconnected,
                                       on_error=plugin.frontend.emitBackendDisconnected,
                                       on_open=lambda: plugin.worker.run_thread_safe(on_connected()))
        except Exception as e:
            plugin.logger.error(str(e))

    plugin.worker.run_thread_safe(initialize_backend())
