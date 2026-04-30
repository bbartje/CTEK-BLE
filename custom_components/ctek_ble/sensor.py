import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import CtekCoordinator
from .config_flow import CONF_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Stel sensoren in voor een geconfigureerd CTEK-apparaat."""
    coordinator = CtekCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    address = entry.data[CONF_ADDRESS]
    info = coordinator.data.get(address)
    name = (info.name if info else None) or address

    entities = [
        CTEKVoltageSensor(coordinator, address, name),
        CTEKTemperatureSensor(coordinator, address, name),
        CTEKChargingSensor(coordinator, address, name),
        CTEKBatteryStateSensor(coordinator, address, name),
    ]

    async_add_entities(entities)


def _get_raw_manufacturer_data(info) -> bytes | None:
    """Haal de eerste manufacturer data bytes op uit een BluetoothServiceInfoBleak."""
    if not info or not info.advertisement:
        return None
    mdata = info.advertisement.manufacturer_data
    if not mdata:
        return None
    return list(mdata.values())[0]


def parse_data(data: bytes) -> tuple[float | None, int | None]:
    """
    Parseer ruwe BLE manufacturer data naar spanning en temperatuur.

    Byte 0-1 (little-endian): spanning * 2048
    Byte 2:                    temperatuur + 17 (offset)
    """
    if not data or len(data) < 3:
        return None, None

    voltage = int.from_bytes(data[0:2], "little") / 2048
    temperature = data[2] - 17
    return voltage, temperature


class BaseSensor(CoordinatorEntity, SensorEntity):
    """Basisklasse voor CTEK BLE sensoren."""

    def __init__(
        self,
        coordinator: CtekCoordinator,
        address: str,
        device_name: str,
        sensor_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._address = address
        self._attr_unique_id = f"{address}_{sensor_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=device_name,
        )

    def _raw_data(self) -> bytes | None:
        info = self.coordinator.data.get(self._address)
        return _get_raw_manufacturer_data(info)


class CTEKVoltageSensor(BaseSensor):
    """Spanning van de accu in Volt."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name, "voltage")
        self._attr_name = f"{name} Voltage"

    @property
    def native_value(self) -> float | None:
        raw = self._raw_data()
        if raw is None:
            return None
        v, _ = parse_data(raw)
        return v


class CTEKTemperatureSensor(BaseSensor):
    """Temperatuur van de accu in °C."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name, "temperature")
        self._attr_name = f"{name} Temperature"

    @property
    def native_value(self) -> int | None:
        raw = self._raw_data()
        if raw is None:
            return None
        _, t = parse_data(raw)
        return t


class CTEKChargingSensor(BaseSensor):
    """Geeft aan of de accu aan het laden is (spanning > 13.6V)."""

    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name, "charging")
        self._attr_name = f"{name} Charging"

    @property
    def native_value(self) -> bool | None:
        raw = self._raw_data()
        if raw is None:
            return None
        v, _ = parse_data(raw)
        if v is None:
            return None
        return v > 13.6


class CTEKBatteryStateSensor(BaseSensor):
    """Kwalitatieve accustatus op basis van spanning."""

    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name, "battery_state")
        self._attr_name = f"{name} Battery State"

    @property
    def native_value(self) -> str | None:
        raw = self._raw_data()
        if raw is None:
            return None
        v, _ = parse_data(raw)
        if v is None:
            return None
        if v < 11.8:
            return "critical"
        if v < 12.2:
            return "low"
        return "ok"
