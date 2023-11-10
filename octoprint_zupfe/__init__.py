# coding=utf-8
from __future__ import absolute_import

import asyncio
import datetime
import hashlib

import flask
import octoprint.plugin
from flask import jsonify

from .FileObject import FileObject
from .constants import EVENT_PRINTER_LINKED, EVENT_PRINTER_UNLINKED, EVENT_OCTOPRINT_SHOW_WIZARD, \
    EVENT_REQUEST_GET_FILE_LIST, EVENT_RTC_OFFER, EVENT_REQUEST_STREAM, \
    EVENT_PRINTER_FILES_UPDATED, EVENT_PRINTER_FILE_SELECTED, EVENT_PRINTER_PRINTING, EVENT_REQUEST_GET_STATE, \
    EVENT_PRINTER_PAUSED, EVENT_PRINTER_CANCELED, EVENT_PRINTER_OPERATIONAL, EVENT_REQUEST_PRINT_ACTIVE_FILE, \
    EVENT_REQUEST_DOWNLOAD_FILE, EVENT_REQUEST_SET_ACTIVE_FILE, EVENT_REQUEST_ABORT_PRINT, EVENT_REQUEST_PROGRESS, \
    EVENT_PRINTER_PRINT_DONE
from .frontend import Frontend
from .p2p_raw_connection import AIORTC_AVAILABLE, accept_p2p_offer, get_p2p_reply
from .request import request_get, request_get_binary, request_get_json, request_post_json
from .worker import AsyncTaskWorker
from .zupfe import Backend


def compute_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            md5.update(block)
    return md5.hexdigest()


class ZupfePlugin(
    octoprint.plugin.BlueprintPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.WizardPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.ProgressPlugin,
    octoprint.plugin.AssetPlugin):

    def __init__(self):
        super().__init__()
        self._default_webcam = None
        self._backend = None
        self._frontend = None
        self._messaging = None
        self._id = None
        self._api_key = None
        self._printer_title = None
        self._print_progress = 0
        self._print_line = 0
        self._worker = AsyncTaskWorker()
        self._p2ps = dict()

    # ------------------------------------------------------------------------------------------------------------------
    # BlueprintPlugin
    # ------------------------------------------------------------------------------------------------------------------

    @octoprint.plugin.BlueprintPlugin.route("/link", methods=["DELETE"])
    def delete_link(self):
        if not self._backend.is_connected() or self._backend.octo_id is None:
            return None
        self._worker.run_thread_safe(self._backend.unlink())
        return None

    @octoprint.plugin.BlueprintPlugin.route("/connection/status", methods=["GET"])
    def get_connection_status(self):
        if not self._backend.is_connected() or self._backend.octo_id is None:
            return {'status': "offline"}
        return {'status': "online"}

    @octoprint.plugin.BlueprintPlugin.route("/urls", methods=["GET"])
    def get_urls(self):
        if not self._backend.is_initialized():
            return flask.abort(503)
        return jsonify(self._backend.urls)

    # ------------------------------------------------------------------------------------------------------------------
    # Others
    # ------------------------------------------------------------------------------------------------------------------
    async def list_files(self):
        # use REST api to fetch also last print date information, not available through file_manager
        api_url = "http://localhost:" + str(self._port) + "/api/files?recursive=true"
        headers = {
            "X-Api-Key": self._settings.global_get(["api", "key"])
        }
        response = await request_get_json(api_url, headers=headers)

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
            api_url = "http://localhost:" + str(self._port) + "/api/files/local/" + data['job']['file']['path']
            headers = {
                "X-Api-Key": self._settings.global_get(["api", "key"])
            }
            active_file = await request_get_json(api_url, headers=headers)

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

        return {
            'activeFile': active_file,
            'activeState': data['state']['text'],
            'state': state
        }

    async def take_snapshot(self):
        if self._default_webcam.config.canSnapshot and self._default_webcam.config.compat is not None:
            snapshot_url = self._default_webcam.config.compat.snapshot
            snapshot_config = self._default_webcam.config
            data = await request_get_binary(snapshot_url, max_retries=1)
            config = {
                'flip_h': snapshot_config.flipH,
                'flip_v': snapshot_config.flipV,
                'rotate_90': snapshot_config.rotate90,
            }
            snapshot = {
                'data': data,
                'config': config
            }
            return snapshot

        return None

    def get_printer_title(self):
        # Get the appearance settings
        appearance_settings = self._settings.global_get(['appearance'])

        # Get the printer title from the appearance settings
        return appearance_settings.get('name', 'Default Printer Title')

    def on_message(self, message, reply, reject):
        async def on_request_p2p():
            offer = message['offer']
            # rtc_id = message['rtcId']
            if AIORTC_AVAILABLE:
                try:
                    p2p = await accept_p2p_offer(self.on_message, offer)
                    answer = get_p2p_reply(p2p)
                    reply(answer)
                except Exception as e:
                    reply(None)
            else:
                reply(None)

        async def on_linked():
            self.save_to_settings_if_updated('linked', True)
            self._frontend.emitOctoprintLinked()

        async def on_unlinked():
            self.save_to_settings_if_updated('linked', False)
            self._frontend.emitOctoprintUnlinked()

        async def on_request_file_stream():
            filename = message['filename']

            if not filename.endswith('.gcode'):
                filename = filename + '.gcode'

            chunk_size = 1024 * 128
            file_manager = self._file_manager
            file_path = file_manager.path_on_disk('local', filename)
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:  # End of file
                        reply(None)
                        break
                    reply(chunk)

        async def on_request_file_list():
            files = await self.list_files()
            reply(files)

        async def no_op():
            pass

        async def on_request_state():
            state = await self.get_current_state()
            reply(state)

        async def on_request_print_active():
            state = await self.get_current_state()
            if not state['state']['printing']:
                self._printer.start_print()
            reply(state)

        async def on_request_abort_print():
            state = await self.get_current_state()
            if state['state']['printing']:
                self._printer.cancel_print()
            reply(state)

        async def on_request_download_file():
            filename = message['filename']

            signed_url = message['signedUrl']
            data = await request_get_binary(signed_url)
            file_manager = self._file_manager
            try:
                file_object = FileObject(data)
                original_filename = filename

                if not filename.endswith('.gcode'):
                    filename = filename + '.gcode'

                file_manager.add_file('local', filename, file_object, allow_overwrite=True)

                if not original_filename == filename:
                    file_manager.set_additional_metadata('local', filename, 'original_filename', original_filename)

                reply(None)
            except Exception as e:
                reject(str(e))

        async def on_request_set_active_file():
            filename = message['filename']

            if not filename.endswith('.gcode'):
                filename = filename + '.gcode'

            file_manager = self._file_manager
            try:
                file_path = file_manager.path_on_disk('local', filename)
                self._printer.select_file(file_path, False)
                reply(None)
            except Exception as e:
                reject(str(e))

        async def on_request_progress():
            progress = self._print_progress
            line = self._print_line
            current_temps = self._printer.get_current_temperatures()

            response = {
                'progress': progress,
                'line': line,
                'temperatures': current_temps
            }
            reply(response)

        handlers = {
            EVENT_PRINTER_LINKED: on_linked,
            EVENT_PRINTER_UNLINKED: on_unlinked,
            EVENT_REQUEST_GET_FILE_LIST: on_request_file_list,
            EVENT_REQUEST_STREAM: on_request_file_stream,
            EVENT_RTC_OFFER: on_request_p2p,
            EVENT_REQUEST_GET_STATE: on_request_state,
            EVENT_REQUEST_PRINT_ACTIVE_FILE: on_request_print_active,
            EVENT_REQUEST_SET_ACTIVE_FILE: on_request_set_active_file,
            EVENT_REQUEST_DOWNLOAD_FILE: on_request_download_file,
            EVENT_REQUEST_ABORT_PRINT: on_request_abort_print,
            EVENT_REQUEST_PROGRESS: on_request_progress,
        }
        handler = handlers.get(message['cmd'])
        if handler is not None:
            self._worker.run_thread_safe(handler())
        else:
            reject('Unknown request ' + message['cmd'])

    # ------------------------------------------------------------------------------------------------------------------
    # SettingsPlugin
    # ------------------------------------------------------------------------------------------------------------------

    def get_settings_defaults(self):
        return {
            'backend_url': 'https://zupfe.velor.ca',
            'frontend_url': 'https://zupfe.velor.ca',
            'linked': False
        }

    def save_to_settings_if_updated(self, name, value):
        cur_value = self.get_from_settings(name, None)
        if cur_value is None or cur_value != value:
            self._logger.info(
                "Value " + str(name) + " has changed so we are updating the value in settings and saving.")
            self._settings.set([name], value, force=True)
            self._settings.save(force=True)

    # Gets the current setting or the default value.
    def get_bool_from_settings(self, name, default):
        value = self._settings.get([name])
        if value is None:
            return default
        return value is True

    # Gets the current setting or the default value.
    def get_from_settings(self, name, default):
        value = self._settings.get([name])
        if value is None:
            return default
        return value

    # ------------------------------------------------------------------------------------------------------------------
    # StartupPlugin
    # ------------------------------------------------------------------------------------------------------------------

    async def on_ready(self):
        if (self._printer_title is None or self._printer_title.strip() == "" or
            self._backend is None or not self._backend.is_initialized()):
            return

        # check the link status after backend has received its urls
        self._logger.debug('Getting link status of current printer')
        link_status = await self._backend.get_link_status()
        self._logger.debug('Status is ' + str(link_status))

        linked = link_status['status'] == 'linked'
        self.save_to_settings_if_updated('linked', linked)

        # update the current printers name after backend has received its urls
        if link_status['name'] is None or link_status['name'] != self._printer_title:
            self._logger.info(
                'Printer name changed from ' + str(link_status['name']) + ' to ' + str(self._printer_title))
            await self._backend.set_printer_title(self._printer_title)

    def on_after_startup(self):
        self._logger.info("Hello World from ZupFe!")

    def on_startup(self, host, port):
        backend_url = self.get_from_settings('backend_url', 'https://zupfe.velor.ca')
        frontend_url = self.get_from_settings('frontend_url', 'https://zupfe.velor.ca')
        self._id = self.get_from_settings('octoprint_id', None)
        self._api_key = self.get_from_settings('api_key', None)
        self._logger.debug("Using backend at " + backend_url + " " + frontend_url)
        self._backend = Backend(backend_url, frontend_url)
        self._frontend = Frontend(self._identifier, self._plugin_manager)
        self._default_webcam = octoprint.webcams.get_snapshot_webcam()
        self._printer_title = self.get_printer_title()

        async def wait_until_next_day():
            await asyncio.sleep(1 * 24 * 60 * 60)
            # await asyncio.sleep(10)

        async def take_snapshots_daily():
            while True:
                try:
                    self._logger.debug('Taking a snapshot from the printer camera')
                    snapshot = await self.take_snapshot()
                    self._logger.debug('Posting the snapshot to ZupFe')
                    await self._backend.post_snapshot(snapshot['config'], snapshot['data'])
                except Exception as e:
                    self._logger.error('Error while taking or sending snapshot ' + str(e))

                await wait_until_next_day()

        async def on_connect():
            self._logger.debug("Connected to websocket")
            try:
                await self.on_ready()
                self._frontend.emitBackendConnected()
            except Exception as e:
                self._logger.error(str(e))

        async def init_backend():
            await self._backend.init()
            self._frontend.emitInitialized()

            linked = False
            if self._id is None:
                self._logger.debug('No octoid, asking for a new one')
                instance = await self._backend.new_octo_id()
                self._id = instance['uuid']
                self._api_key = instance['apiKey']
                self._logger.debug('Got a new octoid')
                self.save_to_settings_if_updated('octoprint_id', self._id)
                self.save_to_settings_if_updated('api_key', self._api_key)
                self.save_to_settings_if_updated('linked', False)
            else:
                # FIXME if the octoid was cleaned from the database ie octoprint has never connected for a long time
                #  then require a new octoid
                self._backend.set_octo_id(self._id, self._api_key)

            # take snapshot after backend has received its urls and id
            self._worker.run_thread_safe(take_snapshots_daily())

            try:
                await self.on_ready()

                self._logger.debug('Connecting websocket to backend')
                self._backend.connect_wss(on_message=self.on_message,
                                          on_close=self._frontend.emitBackendDisconnected,
                                          on_error=self._frontend.emitBackendDisconnected,
                                          on_open=lambda: self._worker.run_thread_safe(on_connect()))
            except Exception as e:
                self._logger.error(str(e))

        self._worker.run_thread_safe(init_backend())

    # ------------------------------------------------------------------------------------------------------------------
    # TemplatePlugin
    # ------------------------------------------------------------------------------------------------------------------

    def get_template_vars(self):
        return {
            # 'initialized': self.backend.isInitialized(),
            # 'add_printer_url': self.backend.get_add_printer_url(self.id),
            # 'remove_printer_url': self.backend.get_remove_printer_url(self.id),
            'frontend_url': self.get_from_settings('frontend_url', 'https://zupfe.velor.ca')
        }

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/zupfe.js", "js/constants.js"],
            "less": ["less/zupfe.less"]
        }

    # ------------------------------------------------------------------------------------------------------------------
    # ProgressPlugin
    # ------------------------------------------------------------------------------------------------------------------
    def on_print_progress(self, storage, path, progress):
        self._print_progress = progress

    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, tags, *args, **kwargs):
        if not tags is None:
            for item in tags:
                if item.startswith('fileline:'):
                    self._print_line = int(item.split(':')[1])
                    break

    # ------------------------------------------------------------------------------------------------------------------
    # EventHandlerPlugin
    # ------------------------------------------------------------------------------------------------------------------

    def on_event(self, event, payload):
        if event == "SettingsUpdated":
            title = self.get_printer_title()
            if title != self._printer_title:
                self._printer_title = title
                if self._backend is not None:
                    self._worker.run_thread_safe(self._backend.set_printer_title(title))

        elif event == "UpdatedFiles":
            if self._backend is not None:
                self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_FILES_UPDATED))

        elif event == "FileSelected":
            if self._backend is not None:
                self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_FILE_SELECTED))

        elif event == "PrintStarted":
            self._print_line = 0

        elif event == "PrintDone":
            self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_PRINT_DONE))

        elif event == "PrinterStateChanged":
            if self._backend is not None:
                if payload['state_id'] == 'PRINTING':
                    self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_PRINTING))
                elif payload['state_id'] == 'PAUSED':
                    self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_PAUSED))
                elif payload['state_id'] == 'CANCELLING':
                    self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_CANCELED))
                elif payload['state_id'] == 'OPERATIONAL':
                    self._print_progress = 0
                    self._worker.run_thread_safe(self._backend.post_event(EVENT_PRINTER_OPERATIONAL))

    # ------------------------------------------------------------------------------------------------------------------
    # WizardPlugin
    # ------------------------------------------------------------------------------------------------------------------

    # # Return true if the wizard needs to be shown.
    def is_wizard_required(self):
        # We don't need to show the wizard if we know current instance is linked.
        return not self.get_bool_from_settings('linked', False)

    # Increment this if we need to pop the wizard again.
    def get_wizard_version(self):
        return 3

    def get_wizard_details(self):
        return {}

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "zupfe": {
                "displayName": "ZupFe For Octoprint",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "glennerichall",
                "repo": "OctoPrint-Zupfe",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/glennerichall/OctoPrint-Zupfe/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "ZupFe For Octoprint"

# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

__plugin_privacypolicy__ = "https://zupfe.velor.ca/privacy.html"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ZupfePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.on_gcode_sent,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
