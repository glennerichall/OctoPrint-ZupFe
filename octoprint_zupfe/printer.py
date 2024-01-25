import asyncio
import json
import logging

logger = logging.getLogger("octoprint.plugins.zupfe")


class Printer:

    def __init__(self, printer, api, settings):
        self._has_psu = None
        self._is_power_on = None
        self._printer = printer
        self._api = api
        self._settings = settings

    def set_power_state(self, power_state):
        self._has_psu = True
        self._is_power_on = power_state['isPSUOn']

    def get_title(self):
        appearance_settings = self._settings.global_get(['appearance'])
        return appearance_settings.get('name', 'Default Printer Title')

    def select_file(self, filename):
        self._printer.select_file(filename, False)

    def start_print(self):
        self._printer.start_print()

    def cancel_print(self):
        self._printer.cancel_print()

    def pause_print(self):
        self._printer.pause_print()

    def resume_print(self):
        self._printer.resume_print()

    async def connect(self):
        self._printer.connect()

    async def power_on(self):
        logger.debug("turning on printer")
        data = json.dumps({"command": "turnPSUOn"})
        response = await self._api.post("/plugin/psucontrol", data=data)
        if response.status() in range(200, 300):
            logger.debug("Operation succeeded")
            await response.close()
        else:
            logger.debug("Operation failed %s", str(response.json()))

    async def power_off(self):
        logger.debug("turning off printer")
        data = json.dumps({"command": "turnPSUOff"})
        response = await self._api.post("/plugin/psucontrol", data=data)
        if response.status() in range(200, 300):
            logger.debug("Operation succeeded")
            await response.close()
        else:
            logger.debug("Operation failed %s", str(response.json()))

    def get_current_temperatures(self):
        return self._printer.get_current_temperatures()

    async def get_state(self):
        data = self._printer.get_current_data()
        active_file = None
        if data['job']['file']['name'] is not None:
            response = await self._api.get("/files/local/" + data['job']['file']['path'])
            active_file = await response.json()
            active_file = active_file['path']

        state = data['state']['flags']
        if self._has_psu is None:
            power_state = await self.read_psu_state()
        else:
            power_state = {
                'hasPSU': self._has_psu,
                'isPSUOn': self._is_power_on
            }

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
                max_retries = 3
                retries = 0
                power_state = None

                # must retry until PSU_CONTROL is bootstrap
                while retries < max_retries:
                    # check if PSU_CONTROL is installed by calling its api
                    data = json.dumps({"command": "getPSUState"})
                    response = await self._api.post("/plugin/psucontrol", data=data)

                    # logger.debug('Received PSU response with status ' + str(response.status()))

                    if response.status() in range(200, 300):
                        power_state = await response.json()
                        break
                    else:
                        error = await response.json()
                        logger.error('PSU response error ' + str(error))
                        retries = retries + 1
                        await asyncio.sleep(1)
                # END LOOP

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
                logger.debug(f"Unable to read PSUControl {e}")
                power_state = {
                    'hasPSU': False
                }
                self._has_psu = False
        else:
            power_state = {
                'hasPSU': False
            }
        return power_state
