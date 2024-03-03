import logging
from urllib.parse import urlencode

from octoprint_zupfe.backend.backend_actions_base import BackendActionBase
from octoprint_zupfe.constants import URL_PRINTER_TITLE, \
    URL_PRINTER_STATUS, URL_PRINTER_EVENT, URL_PRINTER_LINK, \
    URL_PRINTERS, URL_PRINTER_SNAPSHOT, URL_PRINTER_VERSION
from octoprint_zupfe.exceptions import NotFoundException, AuthRequiredException, UnAuthorizedException
from octoprint_zupfe.transport.request import request_put

logger = logging.getLogger("octoprint.plugins.zupfe")


class BackendActions(BackendActionBase):
    def __init__(self, backend):
        super().__init__(backend)

    async def new_octo_id(self, version):
        url = self.get_url(URL_PRINTERS)
        data = {'version': version}
        response = await self.post(url, data=data)
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

    async def set_plugin_version(self, version):
        url = self.get_url(URL_PRINTER_VERSION)
        data = {'version': version}
        response = await self.post(url, data=data)
        await response.close()

    async def check_uuid(self):
        try:
            await self.get_link_status()
        except (NotFoundException, AuthRequiredException, UnAuthorizedException) as e:
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
