import asyncio
import logging

from octoprint_zupfe import request_get_binary

logger = logging.getLogger("PRINTERS.plugins.zupfe.snapshots")


async def wait_until_next_day():
    await asyncio.sleep(1 * 24 * 60 * 60)


async def take_snapshot(webcam):
    if (webcam.config.canSnapshot and
        webcam.config.compat is not None):

        snapshot_url = webcam.config.compat.snapshot
        snapshot_config = webcam.config
        data = await request_get_binary(snapshot_url, max_retries=1)
        config = {
            'flip_h': snapshot_config.flipH,
            'flip_v': snapshot_config.flipV,
            'rotate_90': snapshot_config.rotate90,
        }
        snapshot = {
            'data': data,
            'config': config
        }
        return snapshot

    return None


async def take_snapshots_daily(webcam, backend):
    while True:
        try:
            logger.debug('Taking a snapshot from the printer camera')
            snapshot = await take_snapshot(webcam)
            logger.debug('Posting the snapshot to ZupFe')
            await backend.post_snapshot(snapshot['config'], snapshot['data'])
        except Exception as e:
            logger.error('Error while taking or sending snapshot ' + str(e))

        await wait_until_next_day()
