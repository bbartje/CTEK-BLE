import logging
from datetime import timedelta

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)

# BLE advertisements worden passief ontvangen; 30s is ruim genoeg.
SCAN_INTERVAL = timedelta(seconds=30)


class CtekCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.devices: dict = {}

    async def _async_update_data(self) -> dict:
        """Haal de meest recente BLE advertisement-info op voor alle CTEK-apparaten."""
        infos = async_discovered_service_info(self.hass)

        for info in infos:
            uuids = [s.lower() for s in (info.service_uuids or [])]
            if SERVICE_UUID.lower() in uuids:
                self.devices[info.address] = info
                _LOGGER.debug(
                    "CTEK apparaat gevonden: %s (%s)", info.name, info.address
                )

        return self.devices
