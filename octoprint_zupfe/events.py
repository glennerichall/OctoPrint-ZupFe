import logging

from octoprint_zupfe.backend_sync import update_title_if_changed, notify_printer_state_changed

logger = logging.getLogger("octoprint.plugins.zupfe.events")


def handle_event_async(plugin, event, payload):
    plugin.worker.run_thread_safe(handle_event(plugin, event, payload))


async def handle_event(plugin, event, payload):

    if event == "SettingsUpdated":
        await update_title_if_changed(plugin)

    elif event == "UpdatedFiles":
        await notify_printer_state_changed(plugin, event)

    elif event == "FileSelected":
        await notify_printer_state_changed(plugin, event)

    elif event == "PrintDone":
        state = await plugin.printer.get_state()
        active_file = state['activeFile']
        data = {'filename': active_file}
        await notify_printer_state_changed(plugin, event, data)

    elif event == "PrintStarted":
        plugin.progress.update_progress(0)
        plugin.progress.update_position(0)

    elif event == "PrinterStateChanged":
        plugin.logger.debug('Printer state changed ' + payload['state_id'])
        state = await plugin.printer.get_state()
        active_file = state['activeFile']
        data = {'filename': active_file}
        await notify_printer_state_changed(plugin, payload['state_id'], data)
