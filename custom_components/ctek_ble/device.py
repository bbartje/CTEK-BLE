from __future__ import annotations

import asyncio
import logging
from typing import Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import CHAR_UUID

_LOGGER = logging.getLogger(__name__)

RECONNECT_INTERVAL = 15


def parse_data(data: bytes | bytearray) -> tuple[float | None, int | None]:
    if not data or len(data) < 3:
        _LOGGER.debug("Te korte payload (%d bytes): %s", len(data), data.hex())
        return None, None

    voltage     = int.from_bytes(data[0:2], "little") / 2048
    temperature = data[2] - 17
    _LOGGER.debug("Parsed: %.2fV  %d°C  (raw: %s)", voltage, temperature, data.hex())
    return voltage, temperature


class CTEKDevice:
    def __init__(self, ble_device: BLEDevice) -> None:
        self._ble_device  = ble_device
        self._address     = ble_device.address

        self.voltage:     float | None = None
        self.temperature: int   | None = None
        self.available:   bool         = False

        self._callbacks: list[Callable] = []
        self._task: asyncio.Task | None = None

    def add_callback(self, cb: Callable) -> None:
        self._callbacks.append(cb)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.ensure_future(self._run())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()

    def update_ble_device(self, ble_device: BLEDevice) -> None:
        self._ble_device = ble_device

    def _notify_callbacks(self) -> None:
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                _LOGGER.exception("Fout in callback")

    def _on_notify(self, _sender: int, data: bytearray) -> None:
        v, t = parse_data(data)
        if v is not None:
            self.voltage     = round(v, 2)
            self.temperature = t
            self.available   = True
            self._notify_callbacks()

    def _on_disconnect(self, _client: BleakClient) -> None:
        _LOGGER.info("CTEK %s verbroken", self._address)
        self.available = False
        self._notify_callbacks()

    async def _run(self) -> None:
        while True:
            client: BleakClient | None = None
            try:
                _LOGGER.debug("Verbinden met %s …", self._address)

                client = await establish_connection(
                    BleakClient,
                    self._ble_device,
                    self._address,
                    disconnected_callback=self._on_disconnect,
                    max_attempts=3,
                )

                _LOGGER.info("Verbonden met CTEK %s", self._address)
                await client.start_notify(CHAR_UUID, self._on_notify)

                while client.is_connected:
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                _LOGGER.debug("CTEKDevice loop gestopt")
                if client and client.is_connected:
                    await client.disconnect()
                return
            except Exception as err:
                _LOGGER.warning(
                    "Verbindingsfout: %s — herverbinden over %ds",
                    err, RECONNECT_INTERVAL
                )
            finally:
                self.available = False
                self._notify_callbacks()

            await asyncio.sleep(RECONNECT_INTERVAL)
