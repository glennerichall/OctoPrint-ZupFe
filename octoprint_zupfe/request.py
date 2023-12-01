import asyncio
import json
import logging

import aiohttp

from octoprint_zupfe.constants import (EVENT_MESSAGE_RESPONSE, EVENT_STREAM_CONTENT,
                                       EVENT_STREAM_END, EVENT_STREAM_INFO, EVENT_MESSAGE_FAILURE)

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


async def request(url,
                  method,
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
        response = {
            'id': message['id'],
            'cmd': EVENT_MESSAGE_RESPONSE,
            'response': content
        }
        transport.send(json.dumps(response))

    return reply


def create_stream(transport, message):
    id = message['id']

    def stream(content):
        if content is None:
            transport.send(EVENT_STREAM_END.encode('utf-8') + id.encode('utf-8'))
        elif content is dict:
            transport.send(EVENT_STREAM_INFO.encode('utf-8') + id.encode('utf-8') + json.dumps(content))
        else:
            transport.send(EVENT_STREAM_CONTENT.encode('utf-8') + id.encode('utf-8') + content)

    return stream


def create_rejection(transport, message):
    def reject(content):
        response = {
            'id': message['id'],
            'cmd': EVENT_MESSAGE_FAILURE,
            'response': content
        }
        transport.send(json.dumps(response))

    return reject
