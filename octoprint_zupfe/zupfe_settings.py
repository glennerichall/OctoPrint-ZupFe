import octoprint


class ZupfeSettings(octoprint.plugin.SettingsPlugin):

    def get_settings_defaults(self):
        return {
            'backend_url': 'https://zupfe.velor.ca',
            'frontend_url': 'https://zupfe.velor.ca',
            'linked': False,
            'api_key': None,
            'octoprint_id': None
        }

    def save_to_settings_if_updated(self, name, value):
        cur_value = self.get_from_settings(name, None)
        if cur_value is None or cur_value != value:
            self._logger.debug("Value '" + str(name) + "' changed, updating settings")
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
