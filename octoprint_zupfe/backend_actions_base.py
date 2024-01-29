import logging

from .exceptions import NotFoundException, AuthRequiredException, RequestException, UnAuthorizedException

logger = logging.getLogger("octoprint.plugins.zupfe")


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
                url = url.replace(f':{key}', str(value))

        return url

    async def request(self, method, url, data=None, headers=None, max_retries=None):
        if max_retries is None:
            max_retries = self._max_retries
        response = await self._backend.request(method, url, data=data,
                                               headers=headers, max_retries=max_retries)
        if response.status() == 404:
            response.close()
            raise NotFoundException(method, url, data=data, headers=headers)
        elif response.status() == 401:
            response.close()
            raise AuthRequiredException(method, url, data=data, headers=headers)
        elif response.status() == 403:
            response.close()
            raise UnAuthorizedException(method, url, data=data, headers=headers)
        elif not response.ok():
            response.close()
            raise RequestException(response.status(), method, url, data=data, headers=headers)

        return response

    async def get(self, url, headers=None, max_retries=float('inf')):
        return await self.request('GET', url, headers=headers, max_retries=max_retries)

    async def put(self, url, headers=None, data=None, max_retries=float('inf')):
        return await self.request('PUT', url, data=data, headers=headers, max_retries=max_retries)

    async def post(self, url, headers=None, data=None, max_retries=float('inf')):
        return await self.request('POST', url, data=data, headers=headers, max_retries=max_retries)

    async def delete(self, url, headers=None, max_retries=float('inf')):
        return await self.request('DELETE', url, headers=headers, max_retries=max_retries)
