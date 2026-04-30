from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL
from .config_flow import CONF_ADDRESS
from .device import CTEKDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device: CTEKDevice = hass.data[DOMAIN][entry.entry_id]
    address = entry.data[CONF_ADDRESS]
    name    = entry.title

    async_add_entities([
        CTEKVoltageSensor(device, address, name),
        CTEKTemperatureSensor(device, address, name),
        CTEKChargingSensor(device, address, name),
        CTEKBatteryStateSensor(device, address, name),
    ])


class BaseCTEKSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll     = False

    def __init__(self, device: CTEKDevice, address: str, device_name: str, key: str) -> None:
        self._device = device
        self._attr_unique_id = f"{address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=device_name,
        )

    async def async_added_to_hass(self) -> None:
        self._device.add_callback(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self._attr_available = self._device.available
        self.async_write_ha_state()


class CTEKVoltageSensor(BaseCTEKSensor):
    _attr_device_class               = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_suggested_display_precision = 2
    _attr_name                       = "Voltage"

    def __init__(self, device, address, name):
        super().__init__(device, address, name, "voltage")

    @property
    def native_value(self) -> float | None:
        return self._device.voltage


class CTEKTemperatureSensor(BaseCTEKSensor):
    _attr_device_class               = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_name                       = "Temperature"

    def __init__(self, device, address, name):
        super().__init__(device, address, name, "temperature")

    @property
    def native_value(self) -> int | None:
        return self._device.temperature


class CTEKChargingSensor(BaseCTEKSensor):
    _attr_name = "Charging"

    def __init__(self, device, address, name):
        super().__init__(device, address, name, "charging")

    @property
    def native_value(self) -> str | None:
        v = self._device.voltage
        if v is None:
            return None
        return "charging" if v > 13.6 else "idle"


class CTEKBatteryStateSensor(BaseCTEKSensor):
    _attr_name = "Battery State"

    def __init__(self, device, address, name):
        super().__init__(device, address, name, "battery_state")

    @property
    def native_value(self) -> str | None:
        v = self._device.voltage
        if v is None:
            return None
        if v < 11.8:
            return "critical"
        if v < 12.2:
            return "low"
        return "ok"
