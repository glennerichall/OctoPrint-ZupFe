from .zupfe_request import ZupfeRequest


class ZupfePrinter(ZupfeRequest):
    def __init__(self):
        self._has_psu = None
        self._is_power_on = None

    async def connect(self):
        self._printer.connect()

    async def power_on(self):
        await self.request_post("/plugin/psucontrol", data={"command": "turnPSUOn"})

    async def power_off(self):
        await self.request_post("/plugin/psucontrol", data={"command": "turnPSUOff"})

    async def read_psu_state(self):
        if self._has_psu is None or self._has_psu:
            try:
                # check if PSU_CONTROL is installed by calling its api
                power_state = await self.request_post("/plugin/psucontrol",
                                                      data={"command": "getPSUState"})
                if not power_state is None:
                    power_state['hasPSU'] = True
                    self._has_psu = True
                    self._is_power_on = power_state['isPSUOn']
                else:
                    self._logger.debug("Unable to read PSUControl ")
                    power_state = {
                        'hasPSU': False
                    }
                    self._has_psu = False
            except Exception as e:
                self._logger.debug("Unable to read PSUControl " + str(e))
                power_state = {
                    'hasPSU': False
                }
                self._has_psu = False
        else:
            power_state = {
                'hasPSU': False
            }
        return power_state
