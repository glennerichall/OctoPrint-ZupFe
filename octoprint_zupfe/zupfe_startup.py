import octoprint

from . import Backend, Frontend, take_snapshots_daily
from .backend_actions import BackendActions
from .power_state_poll_loop import start_power_state_poll_loop


class ZupfeStartup(octoprint.plugin.StartupPlugin):
    async def on_ready(self):
        if self._printer_title is None or self._printer_title.strip() == "" or self.backend is None or not self.backend.is_initialized():
            return

        # check the link status after backend has received its urls
        self._logger.debug('Getting link status of current printer')
        link_status = await self.actions.get_link_status()
        self._logger.debug('Status is ' + str(link_status))

        linked = link_status['status'] == 'linked'
        self.save_to_settings_if_updated('linked', linked)

        # update the current printers name after backend has received its urls
        if link_status['name'] is None or link_status['name'] != self._printer_title:
            self._logger.info(
                'Printer name changed from ' + str(link_status['name']) + ' to ' + str(self._printer_title))
            await self.actions.set_printer_title(self._printer_title)

    def on_after_startup(self):
        self.worker.run_thread_safe(start_power_state_poll_loop(self.printer(), self.actions))
        self._logger.info("Hello World from ZupFe!")

    def on_startup(self, host, port):
        backend_url = self.get_from_settings('backend_url', 'https://zupfe.velor.ca')
        frontend_url = self.get_from_settings('frontend_url', 'https://zupfe.velor.ca')
        self._logger.debug("Using backend at " + backend_url)
        self._logger.debug("Using frontend at " + frontend_url)
        self._id = self.get_from_settings('octoprint_id', None)
        self._api_key = self.get_from_settings('api_key', None)
        self._default_webcam = octoprint.webcams.get_snapshot_webcam()
        self._printer_title = self.get_printer_title()
        self._port = port
        self._host = host

        self.backend = Backend(backend_url, frontend_url)
        self.frontend = Frontend(self._identifier, self._plugin_manager)
        self.actions = BackendActions(self.backend)

        async def on_connect():
            self._logger.debug("Connected to websocket")
            try:
                await self.on_ready()
                self.frontend.emitBackendConnected()
            except Exception as e:
                self._logger.error(str(e))

        async def init_backend():
            uuid_valid = False
            while not uuid_valid:
                await self.backend.init()
                self.frontend.emitInitialized()

                linked = False
                if self._id is None:
                    self._logger.debug('No octoid, asking for a new one')
                    instance = await self.backend.new_octo_id()
                    self._id = instance['uuid']
                    self._api_key = instance['apiKey']
                    self._logger.debug('Got a new octoid')
                    self.save_to_settings_if_updated('octoprint_id', self._id)
                    self.save_to_settings_if_updated('api_key', self._api_key)
                    self.save_to_settings_if_updated('linked', False)
                else:
                    self.backend.set_octo_id(self._id, self._api_key)

                uuid_valid = await self.backend.check_uuid()
                if not uuid_valid:
                    self._logger.debug('Octoid not found on backend or api key is invalid, flushing octoid')
                    self._id = None
                    self._api_key = None

            # must transmit api key because:
            # jinja may not have access to value when rendering wizard
            # self.settings.settings.plugins.zupfe.api_key in zupfe.js does not seem to get settings everytime
            self.frontend.emitApiKey(self._api_key)

            # take snapshot after backend has received its urls and id
            self.worker.run_thread_safe(take_snapshots_daily(self._default_webcam, self.actions))

            try:
                await self.on_ready()

                self._logger.debug('Connecting websocket to backend')
                self.backend.connect_wss(on_message=self.on_message,
                                         on_close=self.frontend.emitBackendDisconnected,
                                         on_error=self.frontend.emitBackendDisconnected,
                                         on_open=lambda: self.worker.run_thread_safe(on_connect()))
            except Exception as e:
                self._logger.error(str(e))

        self.worker.run_thread_safe(init_backend())
