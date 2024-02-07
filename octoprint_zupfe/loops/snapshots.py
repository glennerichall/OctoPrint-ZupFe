import asyncio
import logging

logger = logging.getLogger("PRINTERS.plugins.zupfe.snapshots")


async def wait_until_next_day():
    await asyncio.sleep(1 * 24 * 60 * 60)


async def snapshots_daily_push_loop(webcam, actions):
    while True:
        try:
            logger.debug('Taking a snapshot from the printer camera')
            snapshot = await webcam.take_snapshot()
            logger.debug('Posting the snapshot to ZupFe')
            await actions.post_snapshot(snapshot['config'], snapshot['data'])
        except Exception as e:
            logger.debug('Error while taking or sending snapshot ' + str(e))

        await wait_until_next_day()
