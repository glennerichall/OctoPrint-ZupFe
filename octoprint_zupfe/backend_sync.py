from octoprint_zupfe import EVENT_PRINTER_FILES_UPDATED, EVENT_PRINTER_FILE_SELECTED, EVENT_PRINTER_PRINT_DONE, \
    EVENT_PRINTER_PRINTING, EVENT_PRINTER_OPERATIONAL, EVENT_PRINTER_CANCELED, EVENT_PRINTER_PAUSED
from octoprint_zupfe.constants import EVENT_PRINTER_CONNECTING


async def update_title_if_changed(plugin):
    title = plugin.printer.get_title()
    if (title is None
        or title.strip() == ""
        or plugin.backend is None
        or not plugin.backend.is_initialized):
        return

    # check the link status after backend has received its urls
    plugin.logger.debug('Getting link status of current printer')
    link_status = await plugin.actions.get_link_status()
    plugin.logger.debug(f'Status is {link_status}')

    linked = link_status['linked'] == 'linked'
    plugin.settings.save_if_updated('linked', linked)

    if (link_status['name'] is None
        or link_status['name'] != title):
        plugin.logger.debug(f'Printer name changed from {link_status["name"]} to {title}')
        await plugin.actions.set_printer_title(title)


async def notify_printer_state_changed(plugin, state, data=None):
    states = {
        'UpdatedFiles': EVENT_PRINTER_FILES_UPDATED,
        'FileSelected': EVENT_PRINTER_FILE_SELECTED,
        'PrintDone': EVENT_PRINTER_PRINT_DONE,
        'PRINTING': EVENT_PRINTER_PRINTING,
        'PAUSED': EVENT_PRINTER_PAUSED,
        'CANCELLING': EVENT_PRINTER_CANCELED,
        'CONNECTING': EVENT_PRINTER_CONNECTING,
        'OPERATIONAL': EVENT_PRINTER_OPERATIONAL
    }
    if plugin.backend is not None and state in states:
        event = states[state]
        await plugin.actions.post_event(event, data=data)
