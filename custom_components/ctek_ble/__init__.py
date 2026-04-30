from __future__ import annotations

import logging

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .config_flow import CONF_ADDRESS
from .device import CTEKDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    address = entry.data[CONF_ADDRESS]

    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(
            f"CTEK {address} niet gevonden via Bluetooth. "
            "Zorg dat het apparaat in bereik is en herstart."
        )

    device = CTEKDevice(ble_device)
    device.start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        device: CTEKDevice = hass.data[DOMAIN].pop(entry.entry_id)
        device.stop()

    return unload_ok
