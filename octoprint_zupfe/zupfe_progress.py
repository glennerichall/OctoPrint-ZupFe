import octoprint


class ZupfeProgress(octoprint.plugin.ProgressPlugin):
    def __init__(self):
        self._print_line = None
        self._print_progress = None

    def on_print_progress(self, storage, path, progress):
        self._print_progress = progress

    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, tags, *args, **kwargs):
        if not tags is None:
            for item in tags:
                if item.startswith('fileline:'):
                    self._print_line = int(item.split(':')[1])
                    break
