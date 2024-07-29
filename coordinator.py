from datetime import timedelta
import aiohttp
import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class XeniaCoffeeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host: str):
        super().__init__(
            _LOGGER,
            hass,
            name="Xenia Coffee Machine",
            update_interval=timedelta(seconds=30),
        )
        self._host = host

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self._host}/api/v2/overview") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": data.get("MA_STATUS"),
                            "group_temperature": data.get("BG_SENS_TEMP_A"),
                            "boiler_temperature": data.get("BB_SENS_TEMP_A"),
                        }
                    else:
                        raise UpdateFailed(f"Error communicating with API: {response.status}")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")