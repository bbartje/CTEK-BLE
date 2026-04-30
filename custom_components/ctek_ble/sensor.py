import asyncio
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature
from .const import DOMAIN
from .ble import discover_devices

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    devices = await discover_devices()
    entities = []

    for dev in devices:
        hass.loop.create_task(dev.run())

        entities.append(CTEKVoltageSensor(dev))
        entities.append(CTEKTemperatureSensor(dev))

    async_add_entities(entities)


class BaseCTEKSensor(SensorEntity):
    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device.name}"

        device.add_callback(self._update)

    def _update(self):
        self.schedule_update_ha_state()


class CTEKVoltageSensor(BaseCTEKSensor):
    _attr_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = "voltage"

    def __init__(self, device):
        super().__init__(device)
        self._attr_name = f"{device.name} Voltage"

    @property
    def state(self):
        return self._device.voltage


class CTEKTemperatureSensor(BaseCTEKSensor):
    _attr_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = "temperature"

    def __init__(self, device):
        super().__init__(device)
        self._attr_name = f"{device.name} Temperature"

    @property
    def state(self):
        return self._device.temperature
