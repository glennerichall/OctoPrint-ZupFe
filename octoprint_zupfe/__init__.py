# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

from .FileObject import FileObject
from .api import ApiBase
from .commands import handle_message
from .constants import EVENT_PRINTER_LINKED, EVENT_PRINTER_UNLINKED, EVENT_OCTOPRINT_SHOW_WIZARD, \
    EVENT_REQUEST_GET_FILE_LIST, EVENT_RTC_OFFER, EVENT_REQUEST_STREAM, \
    EVENT_PRINTER_FILES_UPDATED, EVENT_PRINTER_FILE_SELECTED, EVENT_PRINTER_PRINTING, EVENT_REQUEST_GET_STATE, \
    EVENT_PRINTER_PAUSED, EVENT_PRINTER_CANCELED, EVENT_PRINTER_OPERATIONAL, EVENT_REQUEST_PRINT_ACTIVE_FILE, \
    EVENT_REQUEST_DOWNLOAD_FILE, EVENT_REQUEST_SET_ACTIVE_FILE, EVENT_REQUEST_ABORT_PRINT, EVENT_REQUEST_PROGRESS, \
    EVENT_PRINTER_PRINT_DONE, EVENT_PRINTER_POWER_UP, EVENT_PRINTER_POWER_DOWN
from .file_manager import FileManager
from .frontend import Frontend
from .request import request_get
from .snapshots import take_snapshots_daily
from .webrtc import AIORTC_AVAILABLE, accept_webrtc_offer, get_webrtc_reply
from .worker import AsyncTaskWorker
from .zupfe_api import ZupfeApiPlugin
from .backend import Backend
from .zupfe_events import ZupfeEvents
from .printer import Printer
from .zupfe_progress import ZupfeProgress
from .zupfe_settings import ZupfeSettings
from .zupfe_startup import ZupfeStartup
from .zupfe_state import ZupfeState
from .zupfe_template import ZupfeTemplate
from .zupfe_wizard import ZupfeWizard


class ZupfePlugin(
    ZupfeApiPlugin,
    ZupfeSettings,
    ZupfeWizard,
    ZupfeProgress,
    ZupfeEvents,
    ZupfeTemplate,
    ZupfeStartup,
    octoprint.plugin.AssetPlugin):

    def __init__(self):
        super().__init__()
        self._host = None
        self._port = None
        self._default_webcam = None
        self._messaging = None
        self._id = None
        self._api_key = None
        self._printer_title = None
        self._print_line = None
        self._print_progress = None
        self._file_pos = None
        self.worker = AsyncTaskWorker()
        self.backend = None
        self.actions = None
        self.frontend = None
        self.api = ApiBase(self)

    def file_manager(self):
        return FileManager(self._file_manager, self.api, self._id)

    def printer(self):
        return Printer(self._printer, self.api)

    def on_message(self, message, reply, reject):
        handle_message(self, message, reply, reject)


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
