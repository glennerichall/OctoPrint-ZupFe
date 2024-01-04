import asyncio

from octoprint_zupfe.power_state_poll_loop import logger


async def start_progress_push_loop(progress, actions):
    logger.debug("Starting progress push loop")
    while True:
        try:
            await actions.post_progress(progress.get_progress_with_temperatures())
            await asyncio.sleep(0.2)
        except Exception as e:
            await asyncio.sleep(2)
