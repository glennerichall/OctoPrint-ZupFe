import threading
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("octoprint.plugins.zupfe")


class AsyncTaskWorker:
    def __init__(self, name="AsyncTaskWorker"):
        self._loop = None
        self._loop_ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=name,
        )
        # daemon mode is mandatory so threads get kill when server shuts down
        self._thread.daemon = True
        logger.info(f"Starting thread {self._thread.name}")
        self._thread.start()

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.set_default_executor(
            ThreadPoolExecutor(thread_name_prefix="AsyncTaskWorker_")
        )
        self._loop_ready.set()
        self._loop.run_forever()

    def shutdown(self, **kwargs):
        logger.warning("AsyncTaskWorker shutdown initiated")
        self._loop.stop()
        self._loop.close()
        self._thread.join()

    def submit_coroutine(self, coroutine, *others):
        self._loop_ready.wait()
        asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        for other in others:
            asyncio.run_coroutine_threadsafe(other, self._loop)
