# coding=utf-8
from __future__ import absolute_import

import octoprint
from octoprint.plugin import EventHandlerPlugin, AssetPlugin, ProgressPlugin, StartupPlugin, SettingsPlugin

from .file_object import FileObject
from .api import ApiBase
from .backend_actions import BackendActions
from .commands import handle_message
from .constants import EVENT_PRINTER_LINKED, EVENT_PRINTER_UNLINKED, EVENT_OCTOPRINT_SHOW_WIZARD, \
    EVENT_REQUEST_GET_FILE_LIST, EVENT_RTC_OFFER, EVENT_REQUEST_STREAM, \
    EVENT_PRINTER_FILES_UPDATED, EVENT_PRINTER_FILE_SELECTED, EVENT_PRINTER_PRINTING, EVENT_REQUEST_GET_STATE, \
    EVENT_PRINTER_PAUSED, EVENT_PRINTER_CANCELED, EVENT_PRINTER_OPERATIONAL, EVENT_REQUEST_PRINT_ACTIVE_FILE, \
    EVENT_REQUEST_DOWNLOAD_FILE, EVENT_REQUEST_SET_ACTIVE_FILE, EVENT_REQUEST_ABORT_PRINT, EVENT_REQUEST_PROGRESS, \
    EVENT_PRINTER_PRINT_DONE, EVENT_PRINTER_POWER_UP, EVENT_PRINTER_POWER_DOWN
from .events import handle_event, handle_event_async
from .file_manager import Files
from .frontend import Frontend
from .progress import Progress
from .request import request_get
from .snapshots import take_snapshots_daily
from .webrtc import AIORTC_AVAILABLE, accept_webrtc_offer, get_webrtc_reply
from .worker import AsyncTaskWorker
from .zupfe_api import ZupfeApiPlugin
from .backend import Backend
from .printer import Printer
from .settings import Settings
from .startup import initialize_backend_async, start_poll_loops
from .zupfe_template import ZupfeTemplate
from .zupfe_wizard import ZupfeWizard


class ZupfePlugin(
    ZupfeApiPlugin,
    ZupfeWizard,
    ZupfeTemplate,
    StartupPlugin,
    ProgressPlugin,
    EventHandlerPlugin,
    SettingsPlugin,
    AssetPlugin):

    def __init__(self):
        super().__init__()
        self._host = None
        self._port = None
        self._default_webcam = None
        self._worker = AsyncTaskWorker()
        self._progress = Progress(self)
        self._backend = None

    @property
    def progress(self):
        return self._progress

    @property
    def webcam(self):
        return self._default_webcam

    @property
    def backend(self):
        return self._backend

    @property
    def actions(self):
        return BackendActions(self.backend)

    @property
    def frontend(self):
        return Frontend(self._identifier, self._plugin_manager)

    @property
    def api(self):
        api_key = self._settings.global_get(["api", "key"])
        return ApiBase(self._host, self._port, api_key)

    @property
    def worker(self):
        return self._worker

    @property
    def file_manager(self):
        octo_id = None
        if self.backend is not None:
            octo_id = self.backend.octo_id

        return Files(self.api, self._file_manager, octo_id)

    @property
    def printer(self):
        return Printer(self._printer, self.api, self.settings)

    @property
    def logger(self):
        return self._logger

    @property
    def settings(self):
        return Settings(self._settings)

    def on_event(self, event, payload):
        handle_event_async(self, event, payload)

    def on_startup(self, host, port):
        self._host = host
        self._port = port
        backend_url = self.settings.get('backend_url', 'https://zupfe.velor.ca')
        frontend_url = self.settings.get('frontend_url', 'https://zupfe.velor.ca')
        self._default_webcam = octoprint.webcams.get_snapshot_webcam()
        self._backend = Backend(backend_url, frontend_url)

        self.logger.debug(f"Using backend at {backend_url}")
        self.logger.debug(f"Using frontend at {frontend_url}")

        initialize_backend_async(self)

    def on_after_startup(self):
        start_poll_loops(self)
        self._logger.info("Hello World from ZupFe!")

    def get_settings_defaults(self):
        return {
            'backend_url': 'https://zupfe.velor.ca',
            'frontend_url': 'https://zupfe.velor.ca',
            'linked': False,
            'api_key': None,
            'octoprint_id': None
        }

    def on_print_progress(self, storage, path, progress):
        self.progress.update_progress(progress)

    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, tags, *args, **kwargs):
        self.progress.update_position(tags)


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
