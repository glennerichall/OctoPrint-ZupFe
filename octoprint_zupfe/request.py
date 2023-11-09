import asyncio
import json
import logging

import aiohttp

from octoprint_zupfe.constants import (EVENT_MESSAGE_RESPONSE, EVENT_STREAM_CONTENT,
                                       EVENT_STREAM_END, EVENT_STREAM_INFO, EVENT_MESSAGE_FAILURE)


logger = logging.getLogger("octoprint.plugins.zupfe.backend")


async def request_put_json(url, headers=None, data=None, max_retries=float('inf')):
    return await request_put(url, lambda response: response.json(), headers, data, max_retries=max_retries)


async def request_put(url, unpack, headers=None, data=None, max_retries=float('inf')):
    retries = 0
    ok_status = False
    logger.debug('PUT ' + url)

    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, data=data, headers=headers, ssl=False) as response:
                    if response.ok:
                        ok_status = True
                        if unpack is not None:
                            return await unpack(response)
                        else:
                            return response
                    else:
                        logger.error('Request PUT ' + url + ' failed with status code:', response.status)
        except aiohttp.ClientError as e:
            logger.error('Request PUT ' + url + ' failed with error:', str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.error('Maximum number of retries reached. Request ' + url + ' failed.')
    return None


async def request_post_json(url, headers=None, data=None, max_retries=float('inf')):
    return await request_post(url, lambda response: response.json(), headers, data, max_retries=max_retries)


async def request_post(url, unpack, headers=None, data=None, max_retries=float('inf')):
    retries = 0
    ok_status = False
    logger.debug('POST ' + url)
    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, ssl=False) as response:
                    if response.ok:
                        ok_status = True
                        if unpack is not None:
                            return await unpack(response)
                        else:
                            return response
                    else:
                        logger.info('Request POST ' + url + ' failed with status code: ' + response.status)
        except aiohttp.ClientError as e:
            logger.info('Request POST ' + url + ' failed with error: ' + str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.info('Maximum number of retries reached. Request ' + url + ' failed.')
    return None

async def request_delete(url, unpack, headers=None, data=None, max_retries=float('inf')):
    retries = 0
    ok_status = False
    logger.debug('DELETE ' + url)
    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers, data=data, ssl=False) as response:
                    if response.ok:
                        ok_status = True
                        if unpack is not None:
                            return await unpack(response)
                        else:
                            return response
                    else:
                        logger.info('Request DELETE ' + url + ' failed with status code: ' + response.status)
        except aiohttp.ClientError as e:
            logger.info('Request DELETE ' + url + ' failed with error: ' + str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.info('Maximum number of retries reached. Request ' + url + ' failed.')
    return None


async def request_get_json(url, max_retries=float('inf'), headers=None):
    return await request_get(url, lambda response: response.json(), max_retries=max_retries, headers=headers)


async def request_get_binary(url, max_retries=float('inf'), headers=None):
    return await request_get(url, lambda response: response.read(), max_retries=max_retries, headers=headers)


async def request_get(url, unpack, max_retries=float('inf'), headers=None):
    retries = 0
    ok_status = False
    while retries < max_retries and not ok_status:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False, headers=headers) as response:
                    if response.ok:
                        ok_status = True
                        if unpack is not None:
                            return await unpack(response)
                        else:
                            return response
                    else:
                        logger.info('Request GET:' + url + ' failed with status code:' + str(response.status))
        except aiohttp.ClientError as e:
            logger.info('Request GET failed with error:' + str(e))

        # Increment the number of retries and wait for a while before retrying
        retries += 1
        await asyncio.sleep(1)

    logger.info('Maximum number of retries reached. Request failed.')
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
