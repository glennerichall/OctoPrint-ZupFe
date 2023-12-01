

class BackendActionBase:
    def __init__(self, backend):
        self._backend = backend
        self._max_retries = 3

    def get_url(self, name, params=None, query=None):
        url = self._backend.urls[name]

        if query is not None:
            url += '?' + query

        if params is not None:
            for key, value in params.items():
                url = url.replace(f':{key}', value)

        return url

    async def request(self, method, url, data=None, headers=None, max_retries=None):
        if max_retries is None:
            max_retries = self._max_retries
        return await self._backend.request(method, url, data=data, headers=headers, max_retries=max_retries)

    async def get(self, url, headers=None, max_retries=float('inf')):
        return await self.request('GET', url, headers=headers, max_retries=max_retries)

    async def put(self, url, headers=None, data=None, max_retries=float('inf')):
        return await self.request('PUT', url, data=data, headers=headers, max_retries=max_retries)

    async def post(self, url, headers=None, data=None, max_retries=float('inf')):
        return await self.request('POST', url, data=data, headers=headers, max_retries=max_retries)

    async def delete(self, url, headers=None, max_retries=float('inf')):
        return await self.request('DELETE', url, headers=headers, max_retries=max_retries)

