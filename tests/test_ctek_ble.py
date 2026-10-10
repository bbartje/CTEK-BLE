import asyncio
import sys
import types
from types import SimpleNamespace

import pytest

voluptuous = types.ModuleType("voluptuous")
voluptuous.Required = lambda *args, **kwargs: args[0] if args else kwargs
voluptuous.Optional = lambda *args, **kwargs: args[0] if args else kwargs
voluptuous.In = lambda *args, **kwargs: args[0] if args else kwargs
voluptuous.Schema = lambda *args, **kwargs: args[0] if args else kwargs
sys.modules.setdefault("voluptuous", voluptuous)

# Minimal HA stubs so the config-flow can be imported in a plain test environment.
homeassistant = types.ModuleType("homeassistant")
homeassistant.__path__ = []
config_entries = types.ModuleType("homeassistant.config_entries")


class ConfigFlow:
    VERSION = 1

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def __init__(self, *args, **kwargs):
        self.hass = None

    def _abort_if_unique_id_configured(self):
        return None

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}


class OptionsFlow:
    def __init__(self, config_entry=None):
        self.config_entry = config_entry

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}


config_entries.ConfigFlow = ConfigFlow
config_entries.OptionsFlow = OptionsFlow
config_entries.ConfigEntry = type("ConfigEntry", (), {})
homeassistant.config_entries = config_entries

components = types.ModuleType("homeassistant.components")
bluetooth = types.ModuleType("homeassistant.components.bluetooth")
bluetooth.async_discovered_service_info = lambda hass: []
components.bluetooth = bluetooth
homeassistant.components = components

core = types.ModuleType("homeassistant.core")
core.callback = lambda func: func
homeassistant.core = core

data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
data_entry_flow.FlowResult = dict
homeassistant.data_entry_flow = data_entry_flow

exceptions = types.ModuleType("homeassistant.exceptions")
exceptions.ConfigEntryNotReady = type("ConfigEntryNotReady", (Exception,), {})
homeassistant.exceptions = exceptions

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.components", components)
sys.modules.setdefault("homeassistant.components.bluetooth", bluetooth)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.data_entry_flow", data_entry_flow)
sys.modules.setdefault("homeassistant.exceptions", exceptions)

from custom_components.ctek_ble.config_flow import CtekOptionsFlow
from custom_components.ctek_ble.const import is_ctek_device, normalize_uuid
from custom_components.ctek_ble.device import CTEKDevice
from custom_components.ctek_ble.const import UNLOCK_CHARACTERISTIC_UUID
from custom_components.ctek_ble.protocol import (
    build_sender_unlock_payload,
    normalize_sender_id,
    parse_data,
    parse_temperature,
    parse_voltage_sample,
)


def test_normalize_uuid_removes_braces_and_case():
    assert normalize_uuid("{812CA8ED-A177-4D74-AEFA-70098C5416AF}") == "812ca8ed-a177-4d74-aefa-70098c5416af"
    assert normalize_uuid("812CA8ED-A177-4D74-AEFA-70098C5416AF") == "812ca8ed-a177-4d74-aefa-70098c5416af"


def test_is_ctek_device_accepts_known_identifiers():
    assert is_ctek_device(name="Battery Sense", service_uuids=["0000fff0-0000-1000-8000-00805f9b34fb"]) is True
    assert is_ctek_device(name="CTEK Battery Sense", service_uuids=[]) is True
    assert is_ctek_device(name="Other Sensor", service_uuids=["0000ffe0-0000-1000-8000-00805f9b34fb"]) is False


def test_parse_data_returns_latest_voltage_from_three_byte_records():
    payload = bytes((0x00, 0x30, 0x01, 0x00, 0xC8, 0x02))

    assert parse_data(payload) == 25.0
    assert parse_voltage_sample(payload) == (25.0, 2)
    assert parse_data(bytes((0x00, 0x30, 0x01, 0x00))) is None


def test_parse_temperature_uses_signed_half_degrees_and_app_rounding():
    assert parse_temperature(bytes((0x05,))) == 3
    assert parse_temperature(bytes((0xFB,))) == -2
    assert parse_temperature(bytes((0xFA,))) == -3
    assert parse_temperature(b"") is None


def test_sender_id_unlock_payload_matches_app_handshake():
    assert normalize_sender_id(" 0123456789abcdef ") == "0123456789ABCDEF"
    assert build_sender_unlock_payload("0123456789ABCDEF").hex() == (
        "364f00a32f2623764d5de646853e3b1c"
    )


def test_sender_id_unlock_is_written_before_notify():
    device = CTEKDevice(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF"), "0123456789ABCDEF"
    )
    calls = []

    class MockClient:
        services = SimpleNamespace(services=[])

        async def write_gatt_char(self, uuid, data, response):
            calls.append(("write", uuid, data, response))

        async def start_notify(self, uuid, callback):
            calls.append(("notify", uuid))

    async def start():
        await device._authenticate(MockClient())
        await device._start_notify(MockClient())

    asyncio.run(start())

    assert calls[0] == (
        "write",
        UNLOCK_CHARACTERISTIC_UUID,
        build_sender_unlock_payload("0123456789ABCDEF"),
        True,
    )
    assert calls[1] == ("notify", "a337b4eb-2544-4f94-87c9-f7732e5fe250")


def test_temperature_read_updates_device_value():
    device = CTEKDevice(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF"), "0123456789ABCDEF"
    )

    class MockClient:
        async def read_gatt_char(self, uuid):
            assert uuid == "b5634099-97c4-4f37-adf3-771246e77754"
            return bytes((0x32,))

    asyncio.run(device._read_temperature(MockClient()))

    assert device.temperature == 25
    assert device.available is True


def test_voltage_notify_failure_does_not_escape_connection_session():
    device = CTEKDevice(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF"), "0123456789ABCDEF"
    )

    async def fail_notify(_client):
        raise RuntimeError("notify unavailable")

    device._start_notify = fail_notify

    asyncio.run(device._start_voltage_notify(SimpleNamespace()))


def test_sender_id_unlock_payload_requires_sixteen_ascii_characters():
    with pytest.raises(ValueError):
        build_sender_unlock_payload("too-short")

    with pytest.raises(ValueError):
        build_sender_unlock_payload("0123456789ABCDEé")


def test_voltage_notification_keeps_signed_auxiliary_byte():
    device = CTEKDevice(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF"), "0123456789ABCDEF"
    )

    device._on_notify(0, bytearray((0x00, 0xC8, 0xFE)))

    assert device.voltage == 25.0
    assert device.voltage_auxiliary == -2


def test_start_notify_failure_includes_discovered_gatt_details():
    device = CTEKDevice(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF"), "0123456789ABCDEF"
    )

    class RejectingClient:
        services = SimpleNamespace(
            services=[
                SimpleNamespace(
                    uuid="service-uuid",
                    characteristics=[
                        SimpleNamespace(uuid="characteristic-uuid", properties=["read", "notify"])
                    ],
                )
            ]
        )

        async def start_notify(self, uuid, callback):
            raise RuntimeError("not supported")

    with pytest.raises(RuntimeError) as error:
        asyncio.run(device._start_notify(RejectingClient()))

    message = str(error.value)
    assert "geprobeerd:" in message
    assert "0000fff4-0000-1000-8000-00805f9b34fb" in message
    assert "service-uuid" in message
    assert "characteristic-uuid [notify,read]" in message


def test_start_notify_failure_reads_bleak_service_mapping_values():
    device = CTEKDevice(
        SimpleNamespace(address="AA:BB:CC:DD:EE:FF"), "0123456789ABCDEF"
    )

    class RejectingClient:
        services = SimpleNamespace(
            services={
                1: SimpleNamespace(
                    uuid="service-uuid",
                    characteristics=[
                        SimpleNamespace(
                            uuid="characteristic-uuid", properties=["notify"]
                        )
                    ],
                )
            }
        )

        async def start_notify(self, uuid, callback):
            raise RuntimeError("not supported")

    with pytest.raises(RuntimeError) as error:
        asyncio.run(device._start_notify(RejectingClient()))

    message = str(error.value)
    assert "service-uuid" in message
    assert "characteristic-uuid [notify]" in message


def test_options_flow_handles_missing_config_entry_data_gracefully():
    entry = SimpleNamespace(data=None, options=None)
    flow = CtekOptionsFlow(entry)

    result = asyncio.run(flow.async_step_init())

    assert result["type"] == "form"
    assert result["step_id"] == "init"
