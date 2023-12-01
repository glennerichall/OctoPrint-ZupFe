class ZupfeState:
    def get_progress(self):
        progress = self._print_progress
        file_pos = self._file_pos
        current_temps = self._printer.get_current_temperatures()

        return {
            'progress': progress,
            'filePos': file_pos,
            'temperatures': current_temps
        }

