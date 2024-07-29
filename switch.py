"""Switch platform for Xenia Coffee Machine."""
from __future__ import annotations

import aiohttp
import async_timeout
import json
from datetime import timedelta
import logging
import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryAuthFailed

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

API_ENDPOINT = "/api/v2/overview"
CONTROL_ENDPOINT = "/api/v2/machine/control"
STATUS_MAP = {0: "off", 1: "on", 2: "eco"}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xenia Coffee Machine switch."""
    host = entry.data[CONF_HOST]
    
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="xenia_coffee_machine",
        update_method=lambda: async_update_data(hass, host),
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([XeniaCoffeeMachine(coordinator, host)])

async def async_update_data(hass: HomeAssistant, host: str):
    """Fetch data from API."""
    session = async_get_clientsession(hass)
    url = f"http://{host}{API_ENDPOINT}"
    
    try:
        async with async_timeout.timeout(10):
            async with session.get(url, headers={'Accept': 'application/json'}) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed("Authentication failed")
                response.raise_for_status()
                data = await response.json()
                
                status = data.get("MA_STATUS", 0)
                return {
                    "is_on": status == 1,
                    "status": STATUS_MAP.get(status, "unknown"),
                }
    except aiohttp.ClientError as err:
        raise UpdateFailed(f"Error communicating with API: {err}")

class XeniaCoffeeMachine(CoordinatorEntity, SwitchEntity):
    """Representation of a Xenia Coffee Machine."""

    def __init__(self, coordinator, host):
        """Initialize Xenia."""
        super().__init__(coordinator)
        self._host = host
        self._attr_name = "Xenia"
        self._attr_unique_id = f"xenia_coffee_machine_{host}"

    @property
    def is_on(self) -> bool:
        """Return true if Xenia is on."""
        return self.coordinator.data["is_on"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "status": self.coordinator.data.get("status"),
        }

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:coffee-maker"

    async def async_turn_on(self, **kwargs):
        """Turn Xenia on."""
        await self._control_machine(action="1")

    async def async_turn_off(self, **kwargs):
        """Turn Xenia off."""
        await self._control_machine(action="0")

    async def _control_machine(self, action):
        """Control the coffee machine."""
        session = async_get_clientsession(self.hass)
        url = f"http://{self._host}{CONTROL_ENDPOINT}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        data = json.dumps({"action": action})

        try:
            async with async_timeout.timeout(10):
                async with session.post(url, headers=headers, data=data) as response:
                    response.raise_for_status()
            await asyncio.sleep(5)
            await self.coordinator.async_request_refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error controlling coffee machine: {err}")