import json

from octoprint_zupfe.constants import EVENT_PRINTER_PROGRESS


def createMessage(cmd, content):
    return json.dumps({
        'cmd': cmd,
        **content
    })


class P2PActions:
    def __init__(self, transport):
        self._transport = transport

    def post_progress(self, progress):
        self._transport.send(createMessage(EVENT_PRINTER_PROGRESS, progress))
