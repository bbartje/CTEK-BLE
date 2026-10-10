from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.components.bluetooth import async_ble_device_from_address
    from homeassistant.exceptions import ConfigEntryNotReady

    from .config_flow import CONF_ADDRESS, CONF_SENDER_ID
    from .device import CTEKDevice

    address = entry.data[CONF_ADDRESS]
    sender_id = entry.options.get(
        CONF_SENDER_ID, entry.data.get(CONF_SENDER_ID)
    )
    if not sender_id:
        raise ConfigEntryNotReady(
            "Sender ID ontbreekt. Open de integratieopties en voer de code van de sticker in."
        )

    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(
            f"CTEK {address} niet gevonden via Bluetooth. "
            "Zorg dat het apparaat in bereik is en herstart."
        )

    device = CTEKDevice(ble_device, sender_id)
    device.start()
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        domain_data = hass.data.get(DOMAIN)
        if domain_data and entry.entry_id in domain_data:
            from .device import CTEKDevice

            device: CTEKDevice | None = domain_data.pop(entry.entry_id)
            if device is not None:
                device.stop()
        if domain_data:
            hass.data[DOMAIN] = domain_data
        else:
            hass.data.pop(DOMAIN, None)

    return unload_ok
