from custom_components.ctek_ble.const import is_ctek_device, normalize_uuid
from custom_components.ctek_ble.protocol import parse_data


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
