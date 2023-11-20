import octoprint

from .constants import EVENT_PRINTER_FILES_UPDATED, EVENT_PRINTER_OPERATIONAL, EVENT_PRINTER_CANCELED, \
    EVENT_PRINTER_PAUSED, EVENT_PRINTER_PRINTING, EVENT_PRINTER_PRINT_DONE, EVENT_PRINTER_FILE_SELECTED, \
    EVENT_PRINTER_CONNECTING


class ZupfeEvents(octoprint.plugin.EventHandlerPlugin):
    def on_event(self, event, payload):
        if event == "SettingsUpdated":
            title = self.get_printer_title()
            if title != self._printer_title:
                self._printer_title = title
                if self.backend is not None:
                    self.worker.run_thread_safe(self.backend.set_printer_title(title))

        elif event == "UpdatedFiles":
            if self.backend is not None:
                self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_FILES_UPDATED))

        elif event == "FileSelected":
            if self.backend is not None:
                self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_FILE_SELECTED))

        elif event == "PrintStarted":
            self._print_line = 0

        elif event == "PrintDone":
            self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_PRINT_DONE))

        elif event == "PrinterStateChanged":
            self._logger.debug('Printer state changed ' + payload['state_id'])
            if self.backend is not None:
                if payload['state_id'] == 'PRINTING':
                    self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_PRINTING))
                elif payload['state_id'] == 'PAUSED':
                    self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_PAUSED))
                elif payload['state_id'] == 'CANCELLING':
                    self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_CANCELED))
                elif payload['state_id'] == 'CONNECTING':
                    self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_CONNECTING))
                elif payload['state_id'] == 'OPERATIONAL':
                    self._print_progress = 0
                    self.worker.run_thread_safe(self.backend.post_event(EVENT_PRINTER_OPERATIONAL))
