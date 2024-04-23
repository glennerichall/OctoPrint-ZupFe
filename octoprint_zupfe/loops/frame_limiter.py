import time

class FrameLimiter:
    def __init__(self, max_rate_per_second):
        self._stream_info = {
            'lastFrameTime': 0,
            'frameCount': 0,
            'maxRate': max_rate_per_second,
        }

    def set_max_rate(self, max_rate_per_second):
        self._stream_info['maxRate'] = max_rate_per_second

    def accept(self, points=1):
        current_time = int(time.time() * 1000)
        stream_info = self._stream_info

        elapsed_time = current_time - stream_info['lastFrameTime']
        desired_interval = 1000 / (stream_info['maxRate'] * points)

        if elapsed_time >= desired_interval or stream_info['frameCount'] == 0:
            stream_info['lastFrameTime'] = current_time
            stream_info['frameCount'] += 1
            return True

        return False
