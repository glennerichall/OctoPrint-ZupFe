import asyncio
import json
import logging

import aiohttp

from octoprint_zupfe.constants import (EVENT_MESSAGE_RESPONSE, EVENT_STREAM_CONTENT,
                                       EVENT_STREAM_END, EVENT_STREAM_INFO, EVENT_MESSAGE_FAILURE)
from octoprint_zupfe.message_builder import MessageBuilder

logger = logging.getLogger("octoprint.plugins.zupfe.backend")


class ResponseWrapper:
    def __init__(self, session, response):
        self._session = session
        self._response = response

    async def close(self):
        await self._response.release()
        await self._session.close()

    async def json(self):
        try:
            return await self._response.json()
        finally:
            await self.close()

    async def read(self):
        try:
            return await self._response.read()
        finally:
            await self.close()

    def status(self):
        return self._response.status

    def ok(self):
        return self._response.ok


async def request(method,
                  url,
                  headers=None,
                  data=None,
                  max_retries=float('inf')):
    retries = 0
    ok_status = False
    logger.debug(f'{method}: {url}')

    while retries < max_retries and not ok_status:
        session = aiohttp.ClientSession()

        try:
            response = await session.request(method, url, data=data, headers=headers, ssl=False)
            return ResponseWrapper(session, response)

        except aiohttp.ClientError as e:
            logger.error(f'Request {method} to {url} failed with error: {e}')
            retries += 1
            await asyncio.sleep(1)

    logger.error(f'Maximum number of retries ({max_retries}) reached. Request {method}: {url} failed.')
    return None


async def request_put(url, headers=None,
                      data=None, max_retries=float('inf')):
    return await request('PUT', url, headers=headers,
                         data=data, max_retries=max_retries)


async def request_post(url, headers=None,
                       data=None, max_retries=float('inf')):
    return await request('POST', url, headers=headers,
                         data=data, max_retries=max_retries)


async def request_get(url, headers=None,
                      data=None, max_retries=float('inf')):
    return await request('GET', url, headers=headers,
                         data=data, max_retries=max_retries)


async def request_delete(url, headers=None,
                         data=None, max_retries=float('inf')):
    return await request('DELETE', url, headers=headers,
                         data=data, max_retries=max_retries)


def create_reply(transport, message):
    def reply(content):
        response = MessageBuilder().new_reply(message, content)
        transport.send_binary(response['buffer'])

    return reply


class StreamReply:
    def __init__(self, transport, message):
        content = message.json()
        self._transport = transport
        self._message = message
        self._stream_id = content['streamId']
        self._reply = create_reply(transport, message)

    def start_stream(self, info):
        self._reply(info)

    def end_stream(self):
        response = MessageBuilder().new_stream_end(self._stream_id)
        self._transport.send_binary(response['buffer'])

    def send_chunk(self, chunk):
        response = MessageBuilder().new_stream_chunk(self._stream_id, chunk)
        self._transport.send_binary(response['buffer'])


def create_stream(transport, message):
    return StreamReply(transport, message)


def create_rejection(transport, message):
    def reject(content):
        response = MessageBuilder().new_rejection(message, content)
        transport.send_binary(response['buffer'])

    return reject
