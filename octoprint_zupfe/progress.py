class Progress:
    def __init__(self, plugin):
        self._plugin = plugin
        self._print_line = None
        self._file_pos = None
        self._print_progress = None

    def update_progress(self, value):
        self._print_progress = value

    def update_position(self, tags):
        if isinstance(tags, (int, float)):
            self._file_pos = tags
        else:
            if tags is not None:
                for item in tags:
                    if item.startswith('filepos:'):
                        self._file_pos = int(item.split(':')[1])
                        break

    def get_progress(self):
        progress = self._print_progress
        file_pos = self._file_pos

        return {
            'progress': progress,
            'filePos': file_pos
        }

    async def get_progress_with_temperatures(self):
        progress = self._print_progress
        file_pos = self._file_pos
        current_temps = await self._plugin.printer.get_current_temperatures()

        return {
            'progress': progress,
            'filePos': file_pos,
            'temperatures': current_temps
        }
