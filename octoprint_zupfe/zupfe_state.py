import asyncio
import datetime

import octoprint

from .constants import EVENT_PRINTER_POWER_UP, EVENT_PRINTER_POWER_DOWN
from .utils import compute_md5
from .zupfe_request import ZupfeRequest


class ZupfeState(octoprint.plugin.SettingsPlugin,
                 ZupfeRequest):

    async def power_state_poll_loop(self):
        self._logger.debug("Starting printer power state poll loop")
        old_power_state = self._is_power_on
        while True:
            await self.read_psu_state()
            if not self._has_psu:
                self._logger.debug("Printer has no psu control, quiting poll loop")
                break
            if not old_power_state == self._is_power_on:
                self._logger.debug("Printer power state changed")
                await self.backend.post_event(EVENT_PRINTER_POWER_UP if
                                              self._is_power_on else
                                              EVENT_PRINTER_POWER_DOWN)
            old_power_state = self._is_power_on
            await asyncio.sleep(1)

    def get_progress(self):
        progress = self._print_progress
        file_pos = self._file_pos
        current_temps = self._printer.get_current_temperatures()

        return {
            'progress': progress,
            'filePos': file_pos,
            'temperatures': current_temps
        }

    async def list_files(self):
        # use REST api to fetch also last print date information, not available through file_manager
        response = await self.request_get("files?recursive=true")

        # flatten file list
        stack = response['files']
        files = []
        while len(stack) > 0:
            elem = stack.pop()
            if elem['type'] == 'machinecode':
                files.append(elem)
            elif elem['type'] == 'folder':
                for c in elem['children']:
                    stack.append(c)

        result = []
        file_manager = self._file_manager
        for file in files:
            metadata = file_manager.get_metadata('local', file['path'])

            if 'md5_hash' in metadata:
                md5_hash = metadata['md5_hash']
            else:
                file_path = file_manager.path_on_disk('local', file['path'])
                md5_hash = compute_md5(file_path)
                file_manager.set_additional_metadata('local', file['path'], 'md5_hash', md5_hash)

            filename = file['path']

            if 'original_filename' in metadata:
                filename = metadata['original_filename']

            last_print = None
            if 'prints' in file:
                last_print = file['prints']['last']['date']
                last_print = datetime.datetime.fromtimestamp(last_print).isoformat()
            obj = {
                'filename': filename,
                'size': file['size'],
                'name': file['name'],
                'hash': md5_hash,
                'creation': datetime.datetime.fromtimestamp(file['date']).isoformat(),
                'last_print': last_print,
                'printer_uuid': self._id
            }
            result.append(obj)
        return result

    async def get_current_state(self):
        data = self._printer.get_current_data()
        active_file = None
        if data['job']['file']['name'] is not None:
            active_file = await self.request_get("/files/local/" + data['job']['file']['path'])

        if active_file is not None:
            file_manager = self._file_manager
            file_path = file_manager.path_on_disk('local', active_file['path'])
            metadata = file_manager.get_metadata('local', file_path)

            if not 'md5_hash' in metadata:
                metadata["md5_hash"] = compute_md5(file_path)
                file_manager.set_metadata('local', file_path, metadata)

            if 'original_filename' in metadata:
                filename = metadata['original_filename']
            else:
                filename = active_file['path']

            active_file = {
                'filename': filename,
                'hash': metadata["md5_hash"]
            }

        state = data['state']['flags']
        power_state = await self.read_psu_state()

        return {
            'activeFile': active_file,
            'activeState': data['state']['text'],
            'state': state,
            'power': power_state
        }

    def get_printer_title(self):
        # Get the appearance settings
        appearance_settings = self._settings.global_get(['appearance'])

        # Get the printer title from the appearance settings
        return appearance_settings.get('name', 'Default Printer Title')
