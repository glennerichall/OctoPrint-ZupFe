# import asyncio
# import logging
# import uuid
# from asyncio import Future
#
# from octoprint_zupfe.messaging.message_builder import MessageBuilder
#
# logger = logging.getLogger("octoprint.plugins.zupfe")
#
# try:
#     from aiortc import RTCPeerConnection, RTCSessionDescription
#
#     logger.debug("Loaded aiortc successfully")
#     AIORTC_AVAILABLE = True
#
# except ImportError as e:
#     AIORTC_AVAILABLE = False
#     logger.debug("Loading aiortc failed with error: " + str(e))
#
#
#     class RTCPeerConnection:
#         def __init__(self, *args, **kwargs):
#             raise NotImplementedError("RTCPeerConnection is not available due to import error")
#
#
#     class RTCSessionDescription:
#         def __init__(self, *args, **kwargs):
#             raise NotImplementedError("RTCSessionDescription is not available due to import error")
#
# from octoprint_zupfe.constants import RPC_REQUEST_STREAM
# from octoprint_zupfe.transport.request import create_reply, create_stream, create_rejection
#
#
# # logger = logging.getLogger('aiortc')
# # logger.setLevel(logging.DEBUG)
#
# def get_webrtc_reply(peer_connection):
#     return {
#         "type": peer_connection.localDescription.type,
#         "sdp": peer_connection.localDescription.sdp
#     }
#
#
# class WebrtcClient:
#     def __init__(self, channel, uuid, worker):
#         self.channel = channel
#         self._close_callbacks = []
#         self._uuid = uuid
#         self._worker = worker
#
#
#     @property
#     def type(self):
#         return "webrtc"
#
#     def send_binary(self, data):
#         self._worker.submit_coroutines(self.send_async(data))
#
#     async def send_async(self, data):
#         self.channel.send(data)
#
#     def on_close(self, callback):
#         self._close_callbacks.append(callback)
#         return lambda: self._close_callbacks.remove(callback)
#
#     def close(self):
#         logger.debug(f"WebRTC data channel closed for {self.uuid}")
#         for callback in self._close_callbacks:
#             callback(self)
#
#     @property
#     def uuid(self):
#         return self._uuid
#
#
# async def accept_webrtc_offer(plugin, on_message, offer):
#     peer_connection = RTCPeerConnection()
#     remote_description = RTCSessionDescription(sdp=offer['sdp'], type=offer['type'])
#     await peer_connection.setRemoteDescription(remote_description)
#
#     webrtc_uuid = str(uuid.uuid4())
#
#     @peer_connection.on("datachannel")
#     def on_datachannel(channel):
#         transport = WebrtcClient(channel, webrtc_uuid, plugin.worker)
#
#         @channel.on("close")
#         def on_close():
#             logger.debug('WebRTC Channel closed')
#
#         @peer_connection.on("iceconnectionstatechange")
#         async def on_iceconnectionstatechange():
#             logger.debug(f'WebRTC Ice connection state changed, {peer_connection.iceConnectionState}')
#             if (peer_connection.iceConnectionState == 'disconnected' or
#                 peer_connection.iceConnectionState == 'failed') :
#                 transport.close()
#
#         @channel.on("message")
#         def on_channel_message(message):
#             message = MessageBuilder().unpack(message)
#
#             if message.command == RPC_REQUEST_STREAM:
#                 reply = create_stream(transport, message)
#             else:
#                 reply = create_reply(transport, message)
#
#             reject = create_rejection(transport, message)
#             on_message(message, reply, reject, transport)
#
#     local_description = await peer_connection.createAnswer()
#     await peer_connection.setLocalDescription(local_description)
#
#     future = Future()
#
#     if peer_connection.iceGatheringState == 'complete':
#         future.set_result(peer_connection)
#     else:
#         @peer_connection.on("icegatheringstatechange")
#         def on_icegatheringstatechange():
#             if peer_connection.iceGatheringState == 'complete':
#                 future.set_result(peer_connection)
#                 peer_connection.remove_listener('icegatheringstatechange', on_icegatheringstatechange)
#
#     return await future
