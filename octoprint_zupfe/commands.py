import logging

from .constants import EVENT_PRINTER_LINKED, EVENT_PRINTER_UNLINKED, EVENT_REQUEST_GET_FILE_LIST, EVENT_REQUEST_STREAM, \
    EVENT_RTC_OFFER, EVENT_REQUEST_GET_STATE, EVENT_REQUEST_PRINT_ACTIVE_FILE, EVENT_REQUEST_SET_ACTIVE_FILE, \
    EVENT_REQUEST_DOWNLOAD_FILE, EVENT_REQUEST_ABORT_PRINT, EVENT_REQUEST_PROGRESS, EVENT_REQUEST_POWER_ON, \
    EVENT_REQUEST_POWER_OFF, EVENT_REQUEST_CONNECTION
from .request import request_get
from .webrtc import AIORTC_AVAILABLE, accept_webrtc_offer, get_webrtc_reply

logger = logging.getLogger("octoprint.plugins.zupfe.commands")


def handle_message(plugin, message, reply, reject):
    async def on_request_p2p():
        logger.debug("Receiving webrtc offer")
        offer = message['offer']
        if AIORTC_AVAILABLE:
            try:
                logger.debug("Setting-up ICE connection")
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
        filename = message['filename']

        if not filename.endswith('.gcode'):
            filename = filename + '.gcode'

        chunk_size = 1024 * 128
        file_manager = plugin.file_manager
        file_path = file_manager.path_on_disk(filename)
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:  # End of file
                    reply(None)
                    break
                reply(chunk)

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
        filename = message['filename']
        signed_url = message['signedUrl']
        response = await request_get(signed_url)
        data = response.read()
        file_manager = plugin.file_manager
        try:
            file_manager.save_file(filename, data)
            reply(None)
        except Exception as e:
            reject(str(e))

    async def on_request_set_active_file():
        filename = message['filename']
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
            await plugin.power_on()
            reply(None)
        except Exception as e:
            reject(None)

    async def on_request_power_off():
        try:
            await plugin.power_off()
            reply(None)
        except Exception as e:
            reject(None)

    async def on_request_connect():
        try:
            await plugin.connect()
            reply(None)
        except Exception as e:
            reject(None)

    handlers = {
        EVENT_PRINTER_LINKED: on_linked,
        EVENT_PRINTER_UNLINKED: on_unlinked,
        EVENT_REQUEST_GET_FILE_LIST: on_request_file_list,
        EVENT_REQUEST_STREAM: on_request_file_stream,
        EVENT_RTC_OFFER: on_request_p2p,
        EVENT_REQUEST_GET_STATE: on_request_state,
        EVENT_REQUEST_PRINT_ACTIVE_FILE: on_request_print_active_file,
        EVENT_REQUEST_SET_ACTIVE_FILE: on_request_set_active_file,
        EVENT_REQUEST_DOWNLOAD_FILE: on_request_download_file,
        EVENT_REQUEST_ABORT_PRINT: on_request_abort_print,
        EVENT_REQUEST_PROGRESS: on_request_progress,
        EVENT_REQUEST_POWER_ON: on_request_power_on,
        EVENT_REQUEST_POWER_OFF: on_request_power_off,
        EVENT_REQUEST_CONNECTION: on_request_connect,
    }
    handler = handlers.get(message['cmd'])
    if handler is not None:
        plugin.worker.run_thread_safe(handler())
    else:
        reject('Unknown request ' + message['cmd'])
