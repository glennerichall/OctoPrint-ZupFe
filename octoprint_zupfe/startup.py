from .commands import handle_message
from .snapshots import snapshots_daily_push_loop
from .worker import AsyncTaskWorker
from .backend_sync import update_status_if_changed, notify_power_state_changed


def start_push_poll_loops(plugin):
    worker = AsyncTaskWorker("Loops")

    worker.submit_coroutines(
        # snapshot is sent to the backend to be saved in the database
        snapshots_daily_push_loop(plugin.default_snapshot_webcam, plugin.actions),
    )


def initialize_plugin(plugin):
    plugin.worker.submit_coroutines(initialize_backend(plugin),
                                    initialize_cameras(plugin))


async def initialize_cameras(plugin):
    # Precompute streamable webcams
    for webcam in plugin.webcams:
        await webcam.validate_stream_url_if_mjpeg()


async def on_connected(plugin):
    plugin.logger.debug("Connected to websocket")
    try:
        await update_status_if_changed(plugin)
        plugin.frontend.emitBackendConnected()
    except Exception as e:
        plugin.logger.error(str(e))


async def initialize_backend(plugin):
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
            on_message=lambda message, reply, reject, transport:
            handle_message(plugin, message, reply, reject, transport),
            on_close=plugin.frontend.emitBackendDisconnected,
            on_error=plugin.frontend.emitBackendDisconnected,
            on_open=lambda: plugin.worker.submit_coroutines(on_connected(plugin)))
    except Exception as e:
        plugin.logger.error(str(e))
