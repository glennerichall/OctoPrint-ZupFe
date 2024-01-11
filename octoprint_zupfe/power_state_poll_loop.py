import asyncio
import logging

from octoprint_zupfe import EVENT_PRINTER_POWER_UP, EVENT_PRINTER_POWER_DOWN

logger = logging.getLogger("octoprint.plugins.zupfe")


async def power_state_poll_loop(printer, actions):
    logger.debug("Starting printer power state poll loop")
    old_power_state = printer.is_power_on()
    while True:
        await printer.read_psu_state()
        if not printer.has_psu():
            logger.debug("Printer has no psu control, quiting poll loop")
            break
        if not old_power_state == printer.is_power_on():
            logger.debug("Printer power state changed")
            try:
                await actions.post_event(EVENT_PRINTER_POWER_UP if
                                         printer.is_power_on() else
                                         EVENT_PRINTER_POWER_DOWN)
            except Exception as e:
                logger.debug('Error while taking or sending power state ' + str(e))

        old_power_state = printer.is_power_on()
        await asyncio.sleep(1)
