import json

from . import request
from .request import unpack_json


class ZupfeRequest:
    async def request_get(self, url):
        api_url = "http://localhost:" + str(self._port) + "/api" + url
        headers = {
            "X-Api-Key": self._settings.global_get(["api", "key"])
        }
        response = await request.request_get(api_url, headers=headers, max_retries=3)
        return await unpack_json(response)

    async def request_post(self, url, data):
        api_url = "http://localhost:" + str(self._port) + "/api" + url
        headers = {
            "X-Api-Key": self._settings.global_get(["api", "key"]),
            "content-type": 'application/json'
        }
        response = await request.request_post(api_url,
                                       headers=headers,
                                       data=json.dumps(data),
                                       max_retries=3,
                                       mute=True)
        return await unpack_json(response)
