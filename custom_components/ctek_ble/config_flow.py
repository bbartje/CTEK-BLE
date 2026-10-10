from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, is_ctek_device

_LOGGER = logging.getLogger(__name__)

CONF_ADDRESS = "address"


class CtekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        infos = async_discovered_service_info(self.hass)
        self._discovered = {}
        for info in infos:
            if is_ctek_device(info.name, info.service_uuids):
                label = info.name or info.address
                self._discovered[info.address] = label

        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().upper()
            if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", address):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                name = self._discovered.get(address, f"CTEK {address}")
                return self.async_create_entry(title=name, data={CONF_ADDRESS: address})

        if self._discovered:
            device_options = {
                addr: f"{name} ({addr})"
                for addr, name in self._discovered.items()
            }
            schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(device_options)})
        else:
            schema = vol.Schema(
                {vol.Required(CONF_ADDRESS, default="2C:FC:E4:01:4F:97"): str}
            )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
