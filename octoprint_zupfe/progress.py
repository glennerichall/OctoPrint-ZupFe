import time


class Progress:
    def __init__(self, plugin):
        self._plugin = plugin
        self._print_line = None
        self._file_pos = None
        self._print_progress = None
        self._temperatures = {
            'x': [],
            'bed': {
                'actual': [],
                'target': []
            },
            'tool0': {
                'actual': [],
                'target': []
            },
        }

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

    def updateTemperatures(self, temperatures):
        now = int(time.time_ns() / 1000000)

        def append(key):
            self._temperatures[key]['actual'].append(temperatures[key]['actual'])
            self._temperatures[key]['target'].append(temperatures[key]['target'])

        def pop(key):
            self._temperatures[key]['actual'].pop(0)
            self._temperatures[key]['target'].pop(0)

        append('bed')
        append('tool0')

        self._temperatures['x'].append(now)

        if len(self._temperatures['x']) > 1800:
            self._temperatures['x'].pop(0)
            pop('bed')
            pop('tool0')

    def get_progress(self):
        progress = self._print_progress
        file_pos = self._file_pos

        return {
            'progress': progress,
            'filePos': file_pos
        }

    def get_temperature_history(self):
        return self._temperatures

    def get_progress_with_temperatures(self):
        progress = self._print_progress
        file_pos = self._file_pos
        temperatures = self._plugin.printer.get_current_temperatures()
        self.updateTemperatures(temperatures)

        return {
            'progress': progress,
            'filePos': file_pos,
            'temperatures': temperatures
        }
