class RequestException(Exception):
    def __init__(self, status, method, url, data=None, headers=None):
        super().__init__(f"Error calling: {method}: {url}")
        self._status = status
        self._method = method
        self._url = url
        self._data = data
        self._headers = headers

    @property
    def method(self):
        return self._method

    @property
    def url(self):
        return self._url

    @property
    def data(self):
        return self._data

    @property
    def headers(self):
        return self._headers

    @property
    def status(self):
        return self._status


class NotFoundException(RequestException):
    def __init__(self, method, url, data=None, headers=None):
        super().__init__(404, method, url, data=data, headers=headers)


class AuthRequiredException(RequestException):
    def __init__(self, method, url, data=None, headers=None):
        super().__init__(401, method, url, data=data, headers=headers)
