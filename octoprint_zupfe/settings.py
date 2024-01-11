import logging

logger = logging.getLogger("octoprint.plugins.zupfe")


class Settings:
    def __init__(self, settings):
        self._settings = settings

    def global_get(self, name):
        return self._settings.global_get(name)

    def save_if_updated(self, name, value):
        cur_value = self.get(name, None)
        if cur_value is None or cur_value != value:
            logger.debug("Value '" + str(name) + "' changed, updating settings")
            self._settings.set([name], value, force=True)
            self._settings.save(force=True)

        # Gets the current setting or the default value.

    def get_bool(self, name, default=None):
        value = self._settings.get([name])
        if value is None:
            return default
        return value is True

        # Gets the current setting or the default value.

    def get(self, name, default):
        value = self._settings.get([name])
        if value is None:
            return default
        return value
