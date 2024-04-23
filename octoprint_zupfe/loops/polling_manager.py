from abc import abstractmethod


class PollingManager:
    def __init__(self, plugin, name, interval=1):
        self._name = name
        self._plugin = plugin
        self._thread = None
        self._default_interval = interval

    @property
    def running(self):
        return self._thread is not None and self._thread.running

    def start(self):
        if self._thread is None:
            self._plugin.logger.debug(f'Starting {self._name} thread')
            self._thread = self.create_thread(self._plugin)

        self._thread.start()


    @property
    def name(self):
        return self._name

    @abstractmethod
    def create_thread(self, plugin):
        pass

    def add_recipient(self, transport, interval=1):
        if interval is None:
            interval = self._default_interval

        if not self.running:
            self.start()

        self._plugin.logger.debug(f"Registering transport {transport.uuid} ({transport.type}) to  {self._name} loop at interval {interval}")

        return self._thread.add_transport(transport, interval)

    def remove_recipient(self, transport, *kwargs):
        result = False
        if self._thread is not None:
            self._plugin.logger.debug(f"Unregistering transport {transport.uuid} ({transport.type}) from  {self._name} loop")
            result = self._thread.remove_transport(transport)
            if self._thread.is_done:
                self._plugin.logger.debug(f'Loop {self._name} is done, flushing it')
                self._thread = None

        return result
