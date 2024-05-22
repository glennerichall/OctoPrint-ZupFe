import octoprint


class ZupfeTemplate(octoprint.plugin.TemplatePlugin):
    def get_template_vars(self):
        return {
            'frontend_url': self.settings.get('frontend_url', 'https://zupfe.velor.ca'),
            'backend_url': self.settings.get('backend_url', 'https://backend.zupfe.velor.ca'),
            'octo_id': self.settings.get('octoprint_id', ''),
            'octoprint_zupfe_version': self.version,
        }

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/zupfe.js", "js/constants.js"],
            "less": ["less/zupfe.less"]
        }
