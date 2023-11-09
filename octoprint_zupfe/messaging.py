from octoprint_zupfe import AIORTC_AVAILABLE, P2PConnection


class Messaging:

    def __init__(self, backend):
        self.backend = backend
        self._p2ps = []

    async def acceptP2P(self, message, reply):
        offer = message['offer']
        if AIORTC_AVAILABLE:
            try:
                p2p = P2PConnection(self.on_message)
                answer = await p2p.accept(offer)
                reply(answer)
                self._p2ps.append(p2p)
            except Exception as e:
                reply(None)
        else:
            reply(None)

    async def publish(self, message):
        pass

