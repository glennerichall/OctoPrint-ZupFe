# coding=utf-8
from __future__ import absolute_import

import octoprint
from octoprint.plugin import EventHandlerPlugin, AssetPlugin, ProgressPlugin, StartupPlugin, SettingsPlugin

from .api import ApiBase
from .backend import Backend
from .backend_actions import BackendActions
from .commands import handle_message
from .constants import EVENT_PRINTER_LINKED, EVENT_PRINTER_UNLINKED, EVENT_OCTOPRINT_SHOW_WIZARD, \
    EVENT_PRINTER_FILES_UPDATED, EVENT_PRINTER_FILE_SELECTED, EVENT_PRINTER_PRINTING, \
    EVENT_PRINTER_PAUSED, EVENT_PRINTER_CANCELED, EVENT_PRINTER_OPERATIONAL, \
    EVENT_PRINTER_PRINT_DONE, EVENT_PRINTER_POWER_UP, EVENT_PRINTER_POWER_DOWN
from .events import handle_event, handle_event_async
from .file_manager import Files
from .file_object import FileObject
from .frontend import Frontend
from .message_builder import MessageBuilder
from .mjpeg_stream_manager import MjpegStreamManager
from .printer import Printer
from .progress import Progress
from .request import request_get
from .settings import Settings
from .snapshots import snapshots_daily_push_loop
from .startup import initialize_backend_async, start_push_poll_loops
from .webcam_wrapper import WebcamWrapper
from .webrtc import AIORTC_AVAILABLE, accept_webrtc_offer, get_webrtc_reply
from .worker import AsyncTaskWorker
from .ws_actions import P2PActions
from .zupfe_api import ZupfeApiPlugin
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
        self._webcams = []
        self._host = None
        self._port = None
        self._worker = AsyncTaskWorker("Main Worker")
        self._progress = Progress(self)
        self._backend = None
        self._printerWrapper = None
        self._api = None
        self._stream_manager = None

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def progress(self):
        return self._progress

    @property
    def default_snapshot_webcam(self):
        webcams = self.snapshot_webcams
        if len(webcams) > 0:
            return webcams[0]
        return None

    @property
    def default_stream_webcam(self):
        webcams = self.stream_webcams
        if len(webcams) > 0:
            return webcams[0]
        return None

    @property
    def snapshot_webcams(self):
        webcams = []
        for webcam in self._webcams:
            if webcam.can_snapshot:
                webcams.append(webcam)
        return webcams

    @property
    def stream_webcams(self):
        webcams = []
        for webcam in self._webcams:
            if webcam.can_stream:
                webcams.append(webcam)
        return webcams

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
    def stream_manager(self):
        return self._stream_manager

    @property
    def api(self):
        return self._api

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
        return self._printerWrapper

    @property
    def logger(self):
        return self._logger

    @property
    def settings(self):
        return Settings(self._settings)

    @property
    def p2p(self):
        if self._backend is None:
            return None
        return P2PActions(self)

    @property
    def transport(self):
        if self._backend is None:
            return None
        return self._backend.ws

    @property
    def message_builder(self):
        return MessageBuilder()

    def on_event(self, event, payload):
        handle_event_async(self, event, payload)

    def on_startup(self, host, port):
        self._host = host
        self._port = port
        self._webcams = []

        self.logger.debug(f"Local api is accessible at http://{host}:{port}")

        backend_url = self.settings.get('backend_url', 'https://zupfe.velor.ca')
        frontend_url = self.settings.get('frontend_url', 'https://zupfe.velor.ca')
        api_key = self._settings.global_get(["api", "key"])

        webcams = octoprint.webcams.get_webcams()
        for webcam_name, webcam in webcams.items():
            self._webcams.append(WebcamWrapper(webcam, self))

        self._backend = Backend(backend_url, frontend_url)
        self._api = ApiBase(host, port, api_key)
        self._printerWrapper = Printer(self._printer, self._api, self.settings)

        self.logger.debug(f"Using backend at {backend_url}")
        self.logger.debug(f"Using frontend at {frontend_url}")

        self._stream_manager = MjpegStreamManager(self)

        initialize_backend_async(self)

    def on_after_startup(self):
        self.logger.debug(f"Starting poll loops")
        start_push_poll_loops(self)
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
__plugin_pythoncompat__ = ">=3.7,<4"  # Only Python 3

__plugin_privacypolicy__ = "https://zupfe.velor.ca/privacy.html"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ZupfePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.on_gcode_sent,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
