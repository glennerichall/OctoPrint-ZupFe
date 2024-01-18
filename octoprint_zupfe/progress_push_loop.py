import asyncio

from octoprint_zupfe.power_state_poll_loop import logger


async def temperature_push_loop(printer, progress, actions):
    logger.debug("Starting temperature push loop")
    while True:
        try:
            temperatures = printer.get_current_temperatures()
            progress.updateTemperatures(temperatures)
            await actions.post_temperatures(temperatures)
            await asyncio.sleep(1)
        except Exception as e:
            logger.debug('Error while taking or sending temperature ' + str(e))
            await asyncio.sleep(2)


async def progress_push_loop(progress, actions):
    logger.debug("Starting progress push loop")
    while True:
        try:
            await actions.post_progress(progress.get_progress())
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.debug('Error while taking or sending progress ' + str(e))
            await asyncio.sleep(2)
