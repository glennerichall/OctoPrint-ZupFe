import asyncio
import json
import logging

import aiohttp

from octoprint_zupfe.constants import (EVENT_MESSAGE_RESPONSE, EVENT_STREAM_CONTENT,
                                       EVENT_STREAM_END, EVENT_STREAM_INFO, EVENT_MESSAGE_FAILURE)

logger = logging.getLogger("octoprint.plugins.zupfe.backend")


async def unpack_json(response):
    try:
        return await response.json()
    except Exception as e:
        logger.error("Unable to unpack json from response " + str(e))


async def unpack_binary(response):
    try:
        return await response.read()
    except Exception as e:
        logger.error("Unable to unpack binary data from response " + str(e))


async def request_put(url, headers=None, data=None, max_retries=float('inf')):
    retries = 0
    ok_status = False
    logger.debug('PUT ' + url)

    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, data=data, headers=headers, ssl=False) as response:
                    return response

        except aiohttp.ClientError as e:
            logger.error('Request PUT ' + url + ' failed with error:', str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.error('Maximum number of retries reached. Request ' + url + ' failed.')
    return None


async def request_post(url, headers=None, data=None, max_retries=float('inf'), mute=False):
    retries = 0
    ok_status = False
    if not mute:
        logger.debug('POST ' + url)

    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, ssl=False) as response:
                    return response

        except aiohttp.ClientError as e:
            logger.debug('Request POST ' + url + ' failed with error: ' + str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.debug('Maximum number of retries reached. Request ' + url + ' failed.')
    return None


async def request_delete(url, headers=None, data=None, max_retries=float('inf')):
    retries = 0
    ok_status = False
    logger.debug('DELETE ' + url)
    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers, data=data, ssl=False) as response:
                    return response

        except aiohttp.ClientError as e:
            logger.debug('Request DELETE ' + url + ' failed with error: ' + str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.debug('Maximum number of retries reached. Request ' + url + ' failed.')
    return None


async def request_get(url, max_retries=float('inf'), headers=None):
    retries = 0
    ok_status = False
    while retries <= max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False, headers=headers) as response:
                    return response

        except aiohttp.ClientError as e:
            logger.debug('Request GET failed with error:' + str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.debug('Maximum number of retries reached. Request failed.')
    return None


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
