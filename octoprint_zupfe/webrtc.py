import json
import logging
from asyncio import Future

logger = logging.getLogger("octoprint.plugins.zupfe.p2p")

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription

    logger.debug("Loaded aiortc successfully")
    AIORTC_AVAILABLE = True

except ImportError as e:
    AIORTC_AVAILABLE = False
    logger.debug("Loading aiortc failed with error: " + str(e))

    class RTCPeerConnection:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("RTCPeerConnection is not available due to import error")

    class RTCSessionDescription:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("RTCSessionDescription is not available due to import error")

from .constants import EVENT_REQUEST_STREAM
from .request import create_reply, create_stream, create_rejection


# logger = logging.getLogger('aiortc')
# logger.setLevel(logging.DEBUG)

def get_p2p_reply(peer_connection):
    return {
        "type": peer_connection.localDescription.type,
        "sdp": peer_connection.localDescription.sdp
    }


async def accept_p2p_offer(on_message, offer):
    peer_connection = RTCPeerConnection()
    remote_description = RTCSessionDescription(sdp=offer['sdp'], type=offer['type'])
    await peer_connection.setRemoteDescription(remote_description)

    @peer_connection.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_channel_message(message):
            message = json.loads(message)
            if message['cmd'] == EVENT_REQUEST_STREAM:
                reply = create_stream(channel, message)
            else:
                reply = create_reply(channel, message)

            reject = create_rejection(channel, message)
            on_message(message, reply, reject)

    local_description = await peer_connection.createAnswer()
    await peer_connection.setLocalDescription(local_description)

    future = Future()

    if peer_connection.iceGatheringState == 'complete':
        future.set_result(peer_connection)
    else:
        @peer_connection.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            if peer_connection.iceGatheringState == 'complete':
                future.set_result(peer_connection)
                peer_connection.remove_listener('icegatheringstatechange', on_icegatheringstatechange)

    return await future
