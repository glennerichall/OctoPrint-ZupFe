import logging

from octoprint_zupfe import EVENT_OCTOPRINT_SHOW_WIZARD
from octoprint_zupfe.constants import EVENT_OCTOPRINT_BACKEND_INITIALIZED, EVENT_PRINTER_LINKED, \
    EVENT_PRINTER_UNLINKED, EVENT_OCTOPRINT_BACKEND_CONNECTED, EVENT_OCTOPRINT_BACKEND_DISCONNECTED, \
    EVENT_OCTOPRINT_APIKEY_RECEIVED

logger = logging.getLogger("octoprint.plugins.zupfe")

class Frontend:
    def __init__(self, identifier, plugin_manager):
        self._plugin_manager = plugin_manager
        self._identifier = identifier

    def emitApiKey(self, api_key):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(
                                                     api_key=api_key,
                                                     type=EVENT_OCTOPRINT_APIKEY_RECEIVED)
                                                 )

    def emitInitialized(self):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(type=EVENT_OCTOPRINT_BACKEND_INITIALIZED))

    def emitBackendConnected(self):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(type=EVENT_OCTOPRINT_BACKEND_CONNECTED))

    def emitBackendDisconnected(self):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(type=EVENT_OCTOPRINT_BACKEND_DISCONNECTED))

    def emitShowWizard(self):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(type=EVENT_OCTOPRINT_SHOW_WIZARD))

    def emitOctoprintLinked(self):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(type=EVENT_PRINTER_LINKED))

    def emitOctoprintUnlinked(self):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 dict(type=EVENT_PRINTER_UNLINKED))
