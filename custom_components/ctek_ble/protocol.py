import hashlib
import logging

_LOGGER = logging.getLogger(__name__)
_SENDER_ID_PREFIX = bytes.fromhex("e1da7195eced40e4bc16559e9de73ba4")


def normalize_sender_id(sender_id: str) -> str:
    return "".join(sender_id.split()).upper()


def is_valid_sender_id(sender_id: str) -> bool:
    normalized = normalize_sender_id(sender_id)
    return len(normalized) == 16 and normalized.isascii()


def build_sender_unlock_payload(sender_id: str) -> bytes:
    normalized = normalize_sender_id(sender_id)
    if not is_valid_sender_id(normalized):
        raise ValueError("Sender ID moet precies 16 ASCII-tekens bevatten")
    return hashlib.md5(
        _SENDER_ID_PREFIX + normalized.encode("ascii"), usedforsecurity=False
    ).digest()


def parse_data(data: bytes | bytearray) -> float | None:
    if not data or len(data) < 3 or len(data) % 3:
        _LOGGER.debug("Ongeldige payload (%d bytes): %s", len(data), bytes(data).hex())
        return None

    payload = bytes(data[-3:])
    voltage = int.from_bytes(payload[0:2], "little") / 2048
    _LOGGER.debug("Parsed: %.2fV  (raw: %s)", voltage, payload.hex())
    return voltage
