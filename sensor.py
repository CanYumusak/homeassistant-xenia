from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature, UnitOfPressure, ENERGY_KILO_WATT_HOUR
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from . import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        XeniaTemperatureSensor(coordinator, "group_temperature", "Group Temperature"),
        XeniaTemperatureSensor(coordinator, "boiler_temperature", "Boiler Temperature")
    ])

class XeniaTemperatureSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type, name):
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"Xenia {name}"
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"
        self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def state(self):
        return self.coordinator.data[self._sensor_type]
