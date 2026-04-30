import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)

CONF_ADDRESS = "address"


class CtekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow voor CTEK BLE integratie."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        # Scan naar beschikbare CTEK-apparaten via HA bluetooth
        infos = async_discovered_service_info(self.hass)
        self._discovered = {}
        for info in infos:
            uuids = [s.lower() for s in (info.service_uuids or [])]
            if SERVICE_UUID.lower() in uuids:
                label = info.name or info.address
                self._discovered[info.address] = label
                _LOGGER.debug("Gevonden via scan: %s (%s)", label, info.address)

        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().upper()

            if not address:
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                # Naam ophalen uit scan, anders adres gebruiken
                name = self._discovered.get(address, f"CTEK {address}")

                return self.async_create_entry(
                    title=name,
                    data={CONF_ADDRESS: address},
                )

        # Bouw schema: gevonden apparaten als keuze, anders vrij tekstveld
        if self._discovered:
            device_options = {
                addr: f"{name} ({addr})"
                for addr, name in self._discovered.items()
            }
            schema = vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(device_options)}
            )
            description = "Selecteer je CTEK Battery Sense."
        else:
            # Geen apparaten gevonden via scan — handmatig invoeren
            schema = vol.Schema(
                {vol.Required(CONF_ADDRESS, default="2C:FC:E4:01:4F:97"): str}
            )
            description = (
                "Geen apparaten automatisch gevonden. "
                "Voer het MAC-adres handmatig in (bijv. 2C:FC:E4:01:4F:97)."
            )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={"description": description},
            errors=errors,
        )
