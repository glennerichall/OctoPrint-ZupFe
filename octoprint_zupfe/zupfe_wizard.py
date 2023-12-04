import octoprint


class ZupfeWizard(octoprint.plugin.WizardPlugin):
    # # Return true if the wizard needs to be shown.
    def is_wizard_required(self):
        # We don't need to show the wizard if we know current instance is linked.
        return not self.settings.get_bool('linked', False)

    # Increment this if we need to pop the wizard again.
    def get_wizard_version(self):
        return 5

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
