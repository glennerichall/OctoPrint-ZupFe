import json

from .request import request_get_json, request_post_json


class ZupfeRequest:
    async def request_get(self, url):
        api_url = "http://localhost:" + str(self._port) + "/api" + url
        headers = {
            "X-Api-Key": self._settings.global_get(["api", "key"])
        }
        return await request_get_json(api_url, headers=headers, max_retries=3)

    async def request_post(self, url, data):
        api_url = "http://localhost:" + str(self._port) + "/api" + url
        headers = {
            "X-Api-Key": self._settings.global_get(["api", "key"]),
            "content-type": 'application/json'
        }
        return await request_post_json(api_url,
                                       headers=headers,
                                       data=json.dumps(data),
                                       max_retries=3,
                                       mute=True)
