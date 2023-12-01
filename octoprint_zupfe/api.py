from .request import request


class ApiBase:
    def __init__(self, plugin):
        self._plugin = plugin

    async def request(self, method, url, data=None, headers=None):
        if headers is None:
            headers = {}

        api_url = "http://localhost:" + str(self._plugin._port) + "/api" + url
        headers = {
            **headers,
            "X-Api-Key": self._plugin._settings.global_get(["api", "key"])
        }
        response = await request(method, api_url, headers=headers, data=data, max_retries=3)
        return await response.json()

    async def get(self, url):
        return await self.request('GET', url)

    async def post(self, url, data):
        headers = {
            "content-type": 'application/json'
        }
        return await self.request('GET', url, data=data, headers=headers)
