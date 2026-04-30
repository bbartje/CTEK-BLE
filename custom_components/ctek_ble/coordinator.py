from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import SERVICE_UUID

class CtekCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant):
        super().__init__(hass, None, name="ctek_ble")

        self.devices = {}

    async def async_update_data(self):
        infos = async_discovered_service_info(self.hass)

        for info in infos:
            if SERVICE_UUID.lower() in [s.lower() for s in info.service_uuids or []]:
                self.devices[info.address] = info

        return self.devices
