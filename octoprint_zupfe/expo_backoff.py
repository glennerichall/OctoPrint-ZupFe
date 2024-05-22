import asyncio
import random
import time



class ExponentialBackoff:
    def __init__(self, base_interval=1, max_interval=60, jitter_factor=0.5):
        self.base_interval = base_interval
        self.max_interval = max_interval
        self.jitter_factor = jitter_factor
        self.current_interval = base_interval
        self.last_call_time = time.time()

    def reset(self):
        self.current_interval = self.base_interval

    def consume(self):
        current_time = time.time()
        # Check if wait was called after a 10-minute interval
        if current_time - self.last_call_time >= 600:
            self.reset()
        else:
            # Increase the backoff interval, up to the max_interval
            self.current_interval = min(self.current_interval * 2, self.max_interval)

        # Apply jitter
        jitter = self.current_interval * self.jitter_factor * random.random()
        backoff_with_jitter = self.current_interval + jitter - (self.jitter_factor / 2 * self.current_interval)
        backoff_with_jitter = max(self.base_interval, backoff_with_jitter)

        return backoff_with_jitter, current_time

    def sleep(self):
        backoff_with_jitter, current_time = self.consume()
        time.sleep(backoff_with_jitter)
        self.last_call_time = current_time

    async def sleepAsync(self):
        backoff_with_jitter, current_time = self.consume()
        await asyncio.sleep(backoff_with_jitter)
        self.last_call_time = current_time

