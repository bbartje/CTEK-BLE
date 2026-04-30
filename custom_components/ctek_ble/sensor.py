from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CHAR_UUID, MANUFACTURER, MODEL
from .coordinator import CtekCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = CtekCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for address, info in coordinator.data.items():
        name = info.name or address

        entities.append(CTEKVoltageSensor(coordinator, address, name))
        entities.append(CTEKTemperatureSensor(coordinator, address, name))
        entities.append(CTEKChargingSensor(coordinator, address, name))
        entities.append(CTEKBatteryStateSensor(coordinator, address, name))

    async_add_entities(entities)


def parse_data(data: bytes):
    if len(data) < 3:
        return None, None

    voltage = int.from_bytes(data[0:2], "little") / 2048
    temperature = data[2] - 17
    return voltage, temperature


class BaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, address, name):
        super().__init__(coordinator)
        self._address = address
        self._name = name

        self._attr_device_info = {
            "identifiers": {(DOMAIN, address)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": name,
        }


class CTEKVoltageSensor(BaseSensor):
    _attr_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = "voltage"

    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name)
        self._attr_name = f"{name} Voltage"

    @property
    def state(self):
        info = self.coordinator.data.get(self._address)
        if not info or not info.advertisement:
            return None

        data = info.advertisement.manufacturer_data
        if not data:
            return None

        raw = list(data.values())[0]
        v, _ = parse_data(raw)
        return v


class CTEKTemperatureSensor(BaseSensor):
    _attr_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = "temperature"

    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name)
        self._attr_name = f"{name} Temperature"

    @property
    def state(self):
        info = self.coordinator.data.get(self._address)
        if not info or not info.advertisement:
            return None

        data = info.advertisement.manufacturer_data
        if not data:
            return None

        raw = list(data.values())[0]
        _, t = parse_data(raw)
        return t


class CTEKChargingSensor(BaseSensor):
    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name)
        self._attr_name = f"{name} Charging"

    @property
    def state(self):
        info = self.coordinator.data.get(self._address)
        if not info or not info.advertisement:
            return None

        raw = list(info.advertisement.manufacturer_data.values())[0]
        v, _ = parse_data(raw)

        if v is None:
            return None

        return v > 13.6


class CTEKBatteryStateSensor(BaseSensor):
    def __init__(self, coordinator, address, name):
        super().__init__(coordinator, address, name)
        self._attr_name = f"{name} Battery State"

    @property
    def state(self):
        info = self.coordinator.data.get(self._address)
        if not info or not info.advertisement:
            return None

        raw = list(info.advertisement.manufacturer_data.values())[0]
        v, _ = parse_data(raw)

        if v is None:
            return None

        if v < 11.8:
            return "critical"
        elif v < 12.2:
            return "low"
        else:
            return "ok"
