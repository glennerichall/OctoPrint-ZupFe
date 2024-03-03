import random
import urllib.parse

import aiohttp
import requests

from octoprint_zupfe.transport.request import request_get
from octoprint_zupfe.messaging.message_builder import max_safe_integer_js


async def validate_url(plugin, webcam):
    reasonable_max_frame_size = 1024 * 1024
    mjpeg_url = webcam.stream_url
    mjpeg_url_valid = False

    plugin.logger.debug(f"Validating mjpeg stream for camera {webcam.id} at {mjpeg_url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(mjpeg_url, timeout=10) as resp:
                plugin.logger.debug(f"Connection with camera {webcam.id} at {mjpeg_url} established")
                stream = b''
                async for chunk in resp.content.iter_chunked(1024):
                    stream += chunk

                    # Check if the buffer contains the start and end of a frame
                    start = stream.find(b'\xff\xd8')
                    end = stream.find(b'\xff\xd9', start)

                    if start != -1 and end != -1:
                        plugin.logger.debug(f"Mjpeg frame found for camera {webcam.id} at {mjpeg_url}")
                        mjpeg_url_valid = True
                        break
                    elif len(stream) > reasonable_max_frame_size:
                        plugin.logger.debug(
                            f"No mjpeg frame found for camera {webcam.id} at {mjpeg_url} after {len(stream)} bytes receives")
                        mjpeg_url_valid = False
                        break

    except Exception as e:
        plugin.logger.debug(f"Unable to read stream from {mjpeg_url}: {e}")
        mjpeg_url_valid = False

    if not mjpeg_url_valid:
        plugin.logger.debug(
            f"No mjpeg frame found for camera {webcam.id} at {mjpeg_url}, mjpeg url is invalid or camera can't stream mjpeg")

    return mjpeg_url_valid

class WebcamWrapper:
    def __init__(self, webcam, plugin):
        self._webcam = webcam
        self._mjpeg_url_valid = False
        self._mjpeg_url = None
        self._plugin = plugin
        self._id = random.randint(1, max_safe_integer_js - 1)

    @property
    def id(self):
        return self._id

    @property
    def name(self) -> str:
        return self._webcam.config.displayName

    @property
    def can_snapshot(self) -> bool:
        return self._webcam.config.canSnapshot

    @property
    def can_stream(self) -> bool:
        return self._mjpeg_url_valid

    @property
    def config(self) -> dict:
        webcam_config = self._webcam.config
        config = {
            'flip_h': webcam_config.flipH,
            'flip_v': webcam_config.flipV,
            'rotate_90': webcam_config.rotate90,
        }
        return config

    async def take_snapshot(self):
        if self.can_snapshot:
            config = self._webcam.config

            config = {
                'flip_h': config.flipH,
                'flip_v': config.flipV,
                'rotate_90': config.rotate90
            }

            if self._webcam.config.compat is not None:
                snapshot_url = self.snapshot_url
                response = await request_get(snapshot_url, max_retries=1)
                data = await response.read()

                snapshot = {
                    'data': data,
                    'config': config
                }
                return snapshot

        return None

    @property
    def snapshot_url(self) -> str:
        snapshot_url = None
        if self._webcam.config.compat is not None:
            snapshot_url = self._webcam.config.compat.snapshot

        return snapshot_url

    @property
    def stream_url(self, use_port:bool=True) -> str:

        if self._mjpeg_url is not None:
            return self._mjpeg_url

        webcam = self._webcam

        mjpeg_url = None

        # The compat object is optional but if it exits, use it.
        if webcam.config.compat is not None:
            mjpeg_url = webcam.config.compat.stream

        if mjpeg_url is None and "stream" in webcam.config.extras:
            mjpeg_url = webcam.config.extras['stream']

        self._plugin.logger.error(mjpeg_url)

        # Parse the URL to check if it has protocol and host
        parsed_url = urllib.parse.urlparse(mjpeg_url)

        # If the URL doesn't have a scheme (protocol) or netloc (host),
        # prepend them from the plugin

        if not parsed_url.scheme or not parsed_url.netloc:
            host_without_port = f"localhost"
            mjpeg_url = urllib.parse.urlunparse((parsed_url.scheme or "http", host_without_port, parsed_url.path,
                                                 parsed_url.params, parsed_url.query, parsed_url.fragment))

        self._mjpeg_url = mjpeg_url

        return mjpeg_url

    async def validate_stream_url_if_mjpeg(self):
        self._mjpeg_url_valid = await validate_url(self._plugin, self)

    async def validate_url_as_stream(self):
        return await self.validate_url_as_mjpeg()

    def read_mjpeg_frames(self, on_frames, is_done):
        mjpeg_url = self.stream_url
        stream_id = self.id

        while not is_done():
            resp = None

            try:
                self._plugin.logger.debug("Getting mjpeg stream for camera %s at %s" % (stream_id, mjpeg_url))
                resp = requests.get(mjpeg_url, stream=True)
                stream = b''

                # import time

                # Initialize the start time and frame counter
                # start_time = time.time()
                # frame_count = 0

                for chunk in resp.iter_content(chunk_size=1024):
                    if is_done():
                        break

                    stream += chunk
                    # Check if the buffer contains the start and end of a frame
                    start = stream.find(b'\xff\xd8')
                    end = stream.find(b'\xff\xd9', start)

                    if start != -1 and end != -1:
                        end = end + 2
                        frame = stream[start:end]
                        stream = stream[end:]

                        if not is_done():
                            on_frames(frame)

                        # Frame successfully processed, increment frame count
                        # frame_count += 1

                    # Periodically calculate FPS
                    # if time.time() - start_time >= 1:  # Every second
                    #     fps = frame_count / (time.time() - start_time)
                    #     print(f"FPS: {fps}")
                    #     # Reset counters for the next measurement
                    #     start_time = time.time()
                    #     frame_count = 0

            except Exception as e:
                self._plugin.logger.debug("Unable to read stream from %s: %s" % (mjpeg_url, e))

            finally:
                if resp:
                    resp.close()
