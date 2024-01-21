import logging
import os

from .constants import EVENT_PRINTER_LINKED, EVENT_PRINTER_UNLINKED, \
    RPC_REQUEST_TEMPERATURE_HISTORY, RPC_REQUEST_CONNECTION, RPC_REQUEST_POWER_OFF, RPC_REQUEST_POWER_ON, \
    RPC_REQUEST_PROGRESS, RPC_REQUEST_ABORT_PRINT, RPC_REQUEST_DOWNLOAD_FILE, RPC_REQUEST_SET_ACTIVE_FILE, \
    RPC_REQUEST_PRINT_ACTIVE_FILE, RPC_REQUEST_GET_STATE, RPC_REQUEST_STREAM, RPC_REQUEST_GET_FILE_LIST, \
    get_constant_name, RPC_REQUEST_TOGGLE_POWER, RPC_REQUEST_WEBRTC
from .request import request_get
from .webrtc import AIORTC_AVAILABLE, accept_webrtc_offer, get_webrtc_reply

logger = logging.getLogger("octoprint.plugins.zupfe")


def handle_message(plugin, message, reply, reject):
    async def on_request_p2p():
        logger.debug("Receiving webrtc offer")
        offer = message.json()
        if AIORTC_AVAILABLE:
            try:
                logger.debug("Setting-up ICE connection")
                # if the offer is accepted, webrtc data channel will call back the lambda
                # which in return will call back the current "handle_message" handler, letting
                # webbsocket and webrtc use the same route for message handling.
                p2p = await accept_webrtc_offer(lambda message, reply, reject:
                                                handle_message(plugin, message, reply, reject), offer)
                answer = get_webrtc_reply(p2p)
                logger.debug("Replying webrtc answer")
                reply(answer)
            except Exception as e:
                logger.debug("Unable top reply answer " + str(e))
                reply(None)
        else:
            logger.debug("Aiortc is unavailable, denying offer")
            reply(None)

    async def on_linked():
        plugin.settings.save_if_updated('linked', True)
        plugin.frontend.emitOctoprintLinked()

    async def on_unlinked():
        plugin.settings.save_if_updated('linked', False)
        plugin.frontend.emitOctoprintUnlinked()

    async def on_request_file_stream():
        content = message.json()
        filename = content['data']['filename']

        if not filename.endswith('.gcode'):
            filename = filename + '.gcode'

        chunk_size = 1024 * 128
        file_manager = plugin.file_manager
        file_path = file_manager.path_on_disk(filename)

        if not os.path.isfile(file_path):
            error = {
                'message': 'File does not exist',
                'filename': filename
            }
            reject(error)
        else:
            stream_info = {
                'filename': filename,
                'length': os.path.getsize(file_path)
            }
            reply.start_stream(stream_info)

            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:  # End of file
                        break
                    reply.send_chunk(chunk)

            reply.end_stream()

    async def on_request_file_list():
        files = await plugin.file_manager.list_files()
        reply(files)

    async def no_op():
        pass

    async def on_request_state():
        state = await plugin.printer.get_state()
        active_file = state['activeFile']

        if active_file is not None:
            state['activeFile'] = plugin.file_manager.get_file_info(active_file)

        reply(state)

    async def on_request_print_active_file():
        state = await plugin.printer.get_state()
        if not state['state']['printing']:
            plugin.printer.start_print()
        reply(state)

    async def on_request_abort_print():
        state = await plugin.printer.get_state()
        if state['state']['printing']:  # printing is boolean
            plugin.printer.cancel_print()
        reply(state)

    async def on_request_download_file():
        content = message.json()
        filename = content['filename']
        signed_url = content['signedUrl']
        response = await request_get(signed_url)
        data = await response.read()
        file_manager = plugin.file_manager
        try:
            file_manager.save_file(filename, data)
            reply(None)
        except Exception as e:
            reject(str(e))

    async def on_request_set_active_file():
        content = message.json()
        filename = content['filename']
        file_manager = plugin.file_manager
        try:
            file_path = file_manager.path_on_disk(filename)
            plugin.printer.select_file(file_path)
            reply(None)
        except Exception as e:
            reject(str(e))

    async def on_request_progress():
        progress = await plugin.progress.get_progress_with_temperatures()
        reply(progress)

    async def on_request_power_on():
        try:
            await plugin.printer.power_on()
            reply(None)
        except Exception as e:
            reject(None)

    async def on_request_power_off():
        try:
            await plugin.printer.power_off()
            reply(None)
        except Exception as e:
            reject(None)

    async def on_request_toggle_power():
        try:
            logger.debug('Toggling power')
            if plugin.printer.has_psu():
                if plugin.printer.is_power_on():
                    await plugin.printer.power_off()
                else:
                    await plugin.printer.power_on()
                reply(None)
            else:
                logger.debug('Printer has no PSU controller')
                reject('Print has no PSU controller')
        except Exception as e:
            reject(str(e))

    async def on_request_connect():
        try:
            await plugin.printer.connect()
            reply(None)
        except Exception as e:
            reject(None)

    async def on_request_temperature_history():
        history = plugin.progress.get_temperature_history()
        reply(history)

    handlers = {
        EVENT_PRINTER_LINKED: on_linked,
        EVENT_PRINTER_UNLINKED: on_unlinked,

        RPC_REQUEST_GET_FILE_LIST: on_request_file_list,
        RPC_REQUEST_STREAM: on_request_file_stream,
        RPC_REQUEST_WEBRTC: on_request_p2p,
        RPC_REQUEST_GET_STATE: on_request_state,
        RPC_REQUEST_PRINT_ACTIVE_FILE: on_request_print_active_file,
        RPC_REQUEST_SET_ACTIVE_FILE: on_request_set_active_file,
        RPC_REQUEST_DOWNLOAD_FILE: on_request_download_file,
        RPC_REQUEST_ABORT_PRINT: on_request_abort_print,
        RPC_REQUEST_PROGRESS: on_request_progress,
        RPC_REQUEST_POWER_ON: on_request_power_on,
        RPC_REQUEST_POWER_OFF: on_request_power_off,
        RPC_REQUEST_TOGGLE_POWER: on_request_toggle_power,
        RPC_REQUEST_CONNECTION: on_request_connect,
        RPC_REQUEST_TEMPERATURE_HISTORY: on_request_temperature_history,
    }
    name = get_constant_name(message.command)
    handler = handlers.get(message.command)
    plugin.logger.debug("received message: %s", name)
    if handler is not None:
        plugin.worker.submit_coroutine(handler())
    else:
        plugin.logger.debug("Command does not exist: " + str(message.command))
        reject('Unknown request ' + str(message.command))
