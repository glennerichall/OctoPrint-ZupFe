import logging

logger = logging.getLogger("octoprint.plugins.zupfe.printer")


class Printer:

    def __init__(self, printer, api):
        self._has_psu = None
        self._is_power_on = None
        self._printer = printer
        self._api = api

    def start_print(self):
        self._printer.start_print()

    def cancel_print(self):
        self._printer.cancel_print()

    async def connect(self):
        self._printer.connect()

    async def power_on(self):
        response = await self._api.post("/plugin/psucontrol", data={"command": "turnPSUOn"})
        await response.close()

    async def power_off(self):
        response = await self._api.post("/plugin/psucontrol", data={"command": "turnPSUOff"})
        await response.close()

    async def get_state(self):
        data = self._printer.get_current_data()
        active_file = None
        if data['job']['file']['name'] is not None:
            active_file = await self._api.get("/files/local/" + data['job']['file']['path'])
            active_file = active_file['path']

        state = data['state']['flags']
        power_state = await self.read_psu_state()

        return {
            'activeFile': active_file,
            'activeState': data['state']['text'],
            'state': state,
            'power': power_state
        }

    def is_power_on(self):
        return self._is_power_on

    def has_psu(self):
        return self._has_psu

    async def read_psu_state(self):
        if self._has_psu is None or self._has_psu:
            try:
                # check if PSU_CONTROL is installed by calling its api
                response = await self._api.post("/plugin/psucontrol",
                                                data={"command": "getPSUState"})

                power_state = await response.json()
                if not power_state is None:
                    power_state['hasPSU'] = True
                    self._has_psu = True
                    self._is_power_on = power_state['isPSUOn']
                else:
                    logger.debug("Unable to read PSUControl ")
                    power_state = {
                        'hasPSU': False
                    }
                    self._has_psu = False
            except Exception as e:
                logger.debug("Unable to read PSUControl " + str(e))
                power_state = {
                    'hasPSU': False
                }
                self._has_psu = False
        else:
            power_state = {
                'hasPSU': False
            }
        return power_state
