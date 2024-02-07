import logging

from octoprint_zupfe.backend.backend_sync import update_status_if_changed, notify_printer_state_changed, \
    notify_power_state_changed

logger = logging.getLogger("octoprint.plugins.zupfe")


def handle_event_async(plugin, event, payload):
    plugin.worker.submit_coroutines(handle_event(plugin, event, payload))


async def handle_event(plugin, event, payload):
    plugin.logger.debug("Received event %s %s", event, str(payload))

    if event == "ClientAuthed":
        await update_status_if_changed(plugin)

    elif event == "plugin_psucontrol_psu_state_changed":
        plugin.printer.set_power_state(payload)
        await notify_power_state_changed(plugin)

    elif event == "SettingsUpdated":
        await update_status_if_changed(plugin)

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
