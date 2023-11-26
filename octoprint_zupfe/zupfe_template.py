import octoprint


class ZupfeTemplate(octoprint.plugin.TemplatePlugin):
    def get_template_vars(self):
        return {
            'frontend_url': self.get_from_settings('frontend_url', 'https://zupfe.velor.ca'),
        }

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/zupfe.js", "js/constants.js"],
            "less": ["less/zupfe.less"]
        }
