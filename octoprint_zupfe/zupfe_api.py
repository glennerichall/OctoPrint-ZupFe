import flask
import octoprint
from flask import jsonify


class ZupfeApiPlugin(octoprint.plugin.BlueprintPlugin):

    # ------------------------------------------------------------------------------------------------------------------
    # BlueprintPlugin
    # ------------------------------------------------------------------------------------------------------------------

    @octoprint.plugin.BlueprintPlugin.route("/link", methods=["DELETE"])
    def delete_link(self):
        if not self.backend.is_connected or self.backend.octo_id is None:
            return None
        self.worker.submit_coroutines(self.actions.unlink())
        return {}

    @octoprint.plugin.BlueprintPlugin.route("/connection/status", methods=["GET"])
    def get_connection_status(self):
        if not self.backend.is_connected or self.backend.octo_id is None:
            return {'status': "offline"}
        return {'status': "online"}

    @octoprint.plugin.BlueprintPlugin.route("/urls", methods=["GET"])
    def get_urls(self):
        if not self.backend.is_initialized:
            return flask.abort(503)
        return jsonify(self.backend.urls)
