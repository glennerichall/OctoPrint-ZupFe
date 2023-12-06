import json
from urllib.parse import urlencode

from .backend_actions_base import BackendActionBase
from .constants import URL_PRINTER_TITLE, \
    URL_PRINTER_STATUS, URL_PRINTER_EVENT, URL_PRINTER_LINK, \
    URL_PRINTERS, URL_PRINTER_SNAPSHOT, EVENT_PRINTER_PROGRESS
from .exceptions import NotFoundException, AuthRequiredException
from .request import request_put


class BackendActions(BackendActionBase):
    def __init__(self, backend):
        super().__init__(backend)

    async def new_octo_id(self):
        url = self.get_url(URL_PRINTERS)
        response = await self.post(url)
        instance = await response.json()
        octo_id = instance['uuid']
        api_key = instance['apiKey']
        self._backend.set_octo_id(octo_id, api_key)
        return instance

    async def post_snapshot(self, config, snapshot):
        url = self.get_url(URL_PRINTER_SNAPSHOT, query=urlencode(config))
        response = await self.post(url)
        post_info = await response.json()
        await request_put(post_info['uploadURL'], None, data=snapshot)

    async def post_event(self, event, data=None):
        url = self.get_url(URL_PRINTER_EVENT, params={'event': event})
        response = await self.post(url, data=data)
        await response.close()

    async def set_printer_title(self, title):
        url = self.get_url(URL_PRINTER_TITLE)
        data = {'title': title}
        response = await self.post(url, data=data)
        await response.close()

    async def check_uuid(self):
        try:
            await self.get_link_status()
        except (NotFoundException, AuthRequiredException):
            return False
        return True

    async def get_link_status(self):
        url = self.get_url(URL_PRINTER_STATUS)
        response = await self.get(url)
        return await response.json()

    async def unlink(self):
        url = self.get_url(URL_PRINTER_LINK)
        response = await self.delete(url)
        response.close()
