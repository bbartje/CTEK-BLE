DOMAIN = "ctek_ble"

# The original project hard-coded a single UUID pair, but CTEK Battery Sense modules
# commonly advertise under multiple valid GATT profile combinations and may be seen
# through Home Assistant Bluetooth proxies/gateways. Keep the legacy values for
# backward compatibility while allowing a broader set of valid identifiers.
SERVICE_UUID = "812ca8ed-a177-4d74-aefa-70098c5416af"
CHAR_UUID = "a337b4eb-2544-4f94-87c9-f7732e5fe250"
TEMPERATURE_CHARACTERISTIC_UUID = "b5634099-97c4-4f37-adf3-771246e77754"
UNLOCK_CHARACTERISTIC_UUID = "a1d67c01-fe3f-01bf-7d49-7dbdc43b02a6"

SERVICE_UUIDS = [
    SERVICE_UUID,
    "0000fff0-0000-1000-8000-00805f9b34fb",
    "0000ffe0-0000-1000-8000-00805f9b34fb",
]
CHARACTERISTIC_UUIDS = [
    CHAR_UUID,
    "0000fff4-0000-1000-8000-00805f9b34fb",
    "0000ffe1-0000-1000-8000-00805f9b34fb",
]
CTEK_DEVICE_NAMES = ("battery sense", "ctek battery sense", "battery-sense", "ctek")

MANUFACTURER = "CTEK"
MODEL = "Battery Sense"


def normalize_uuid(value: str | None) -> str | None:
    """Normalize a BLE UUID to a canonical lowercase form."""
    if value is None:
        return None
    cleaned = str(value).strip().replace("{", "").replace("}", "")
    if cleaned.startswith("0x") or cleaned.startswith("0X"):
        cleaned = cleaned[2:]
    return cleaned.lower()


def is_ctek_device(
    name: str | None,
    service_uuids: list[str] | tuple[str, ...] | set[str] | None = None,
) -> bool:
    """Return True for Battery Sense advertisements and known CTEK service IDs."""
    normalized_name = (name or "").strip().lower()
    if normalized_name:
        for candidate in CTEK_DEVICE_NAMES:
            if candidate in normalized_name:
                return True
        return False

    if not service_uuids:
        return False

    normalized = {normalize_uuid(uuid) for uuid in service_uuids if uuid}
    for candidate in SERVICE_UUIDS:
        if normalize_uuid(candidate) in normalized:
            return candidate in (SERVICE_UUID,)

    return False
