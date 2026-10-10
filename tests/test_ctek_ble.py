import asyncio
from types import SimpleNamespace

import pytest

from custom_components.ctek_ble.const import is_ctek_device, normalize_uuid
from custom_components.ctek_ble.device import CTEKDevice
from custom_components.ctek_ble.const import UNLOCK_CHARACTERISTIC_UUID
from custom_components.ctek_ble.protocol import (
    build_sender_unlock_payload,
    normalize_sender_id,
    parse_data,
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
    assert parse_data(bytes((0x00, 0x30, 0x01, 0x00))) is None


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


def test_sender_id_unlock_payload_requires_sixteen_ascii_characters():
    with pytest.raises(ValueError):
        build_sender_unlock_payload("too-short")

    with pytest.raises(ValueError):
        build_sender_unlock_payload("0123456789ABCDEé")


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
