import logging

_LOGGER = logging.getLogger(__name__)


def parse_data(data: bytes | bytearray) -> float | None:
    if not data or len(data) < 3 or len(data) % 3:
        _LOGGER.debug("Ongeldige payload (%d bytes): %s", len(data), bytes(data).hex())
        return None

    payload = bytes(data[-3:])
    voltage = int.from_bytes(payload[0:2], "little") / 2048
    _LOGGER.debug("Parsed: %.2fV  (raw: %s)", voltage, payload.hex())
    return voltage
