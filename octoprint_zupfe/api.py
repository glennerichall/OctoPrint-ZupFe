import logging

from .request import request

logger = logging.getLogger("octoprint.plugins.zupfe")

class ApiBase:
    def __init__(self, host, port, api_key):
        self._host = host
        self._port = port
        self._api_key = api_key

    async def request(self, method, url, data=None, headers=None):
        if headers is None:
            headers = {}

        api_url = f"http://localhost:{self._port}/api{url}"
        headers = {
            **headers,
            "X-Api-Key": self._api_key,
        }
        response = await request(method, api_url, headers=headers, data=data, max_retries=30)
        return response

    async def get(self, url):
        return await self.request('GET', url)

    async def post(self, url, data):
        headers = {
            "content-type": 'application/json'
        }
        return await self.request('POST', url, data=data, headers=headers)
