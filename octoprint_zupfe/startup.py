from . import snapshots_daily_push_loop, handle_message, AsyncTaskWorker
from .backend_sync import update_status_if_changed
from .mjpeg_push_loop import send_mjpeg_to_websocket
from .power_state_poll_loop import power_state_poll_loop
from .progress_push_loop import progress_push_loop, temperature_push_loop


def start_push_poll_loops(plugin):
    worker = AsyncTaskWorker("Loops")

    worker.submit_coroutine(
        # snapshot is sent to the backend to be saved in the database
        snapshots_daily_push_loop(plugin.webcam, plugin.actions),

        # power state is sent to backend like any other printer event
        power_state_poll_loop(plugin.printer, plugin.actions),

        # temperature and progress are intensive traffic, ideally they should be
        # sent through webrtc, but websocket is also acceptable. p2p will switch
        # between webrtc and websocket accordingly.
        temperature_push_loop(plugin.printer, plugin.progress, plugin.p2p),
        progress_push_loop(plugin.progress, plugin.p2p),
    )

    # mjpeg is sent through websocket since it is a fallback from missing webrtc
    # availability in current octoprint instance.
    send_mjpeg_to_websocket(plugin.webcam, lambda: plugin.backend.ws)


def initialize_backend_async(plugin):
    async def on_connected():
        plugin.logger.debug("Connected to websocket")
        try:
            await update_status_if_changed(plugin)
            plugin.frontend.emitBackendConnected()
        except Exception as e:
            plugin.logger.error(str(e))

    async def initialize_backend():
        plugin.logger.debug('Initializing backend')
        await plugin.backend.init()
        plugin.frontend.emitInitialized()

        octo_id = plugin.settings.get('octoprint_id', None)
        api_key = plugin.settings.get('api_key', None)

        uuid_valid = False
        while not uuid_valid:
            if octo_id is None:
                plugin.logger.debug('No octoid, asking for a new one')
                instance = await plugin.actions.new_octo_id()
                plugin.logger.debug('Got a new octoid')
                octo_id = instance['uuid']
                api_key = instance['apiKey']
                plugin.settings.save_if_updated('octoprint_id', octo_id)
                plugin.settings.save_if_updated('api_key', api_key)
                plugin.settings.save_if_updated('linked', False)
            else:
                plugin.backend.set_octo_id(octo_id, api_key)

            plugin.logger.debug('Checking validity of octoid and api key')
            uuid_valid = await plugin.actions.check_uuid()

            if not uuid_valid:
                plugin.logger.debug('Octoid not found on backend or api key is invalid, flushing octoid')
                octo_id = None
                api_key = None
            else:
                plugin.logger.debug('Octoid is valid')

        # must transmit api key because:
        # jinja may not have access to value when rendering wizard
        # self.settings.settings.plugins.zupfe.api_key in zupfe.js does not seem to get settings everytime
        plugin.frontend.emitApiKey(api_key)

        try:

            plugin.logger.debug('Connecting to websocket')
            plugin.backend.connect_wss(
                on_message=lambda message, reply, reject: handle_message(plugin, message, reply, reject),
                on_close=plugin.frontend.emitBackendDisconnected,
                on_error=plugin.frontend.emitBackendDisconnected,
                on_open=lambda: plugin.worker.submit_coroutine(on_connected()))
        except Exception as e:
            plugin.logger.error(str(e))

    plugin.worker.submit_coroutine(initialize_backend())
