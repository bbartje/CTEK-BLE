from __future__ import annotations

import asyncio
import logging
from typing import Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import (
    CHARACTERISTIC_UUIDS,
    CHAR_UUID,
    UNLOCK_CHARACTERISTIC_UUID,
    normalize_uuid,
)
from .protocol import build_sender_unlock_payload, normalize_sender_id, parse_data

_LOGGER = logging.getLogger(__name__)

RECONNECT_INTERVAL = 15


class CTEKDevice:
    def __init__(self, ble_device: BLEDevice, sender_id: str) -> None:
        self._ble_device  = ble_device
        self._address     = ble_device.address
        self._sender_id   = normalize_sender_id(sender_id)

        self.voltage:     float | None = None
        self.available:   bool         = False

        self._callbacks: list[Callable] = []
        self._task: asyncio.Task | None = None

    def add_callback(self, cb: Callable) -> None:
        self._callbacks.append(cb)
        try:
            cb()
        except Exception:
            _LOGGER.exception("Fout bij initialisatie van callback")

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.ensure_future(self._run())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def update_ble_device(self, ble_device: BLEDevice) -> None:
        self._ble_device = ble_device

    def _notify_callbacks(self) -> None:
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                _LOGGER.exception("Fout in callback")

    async def _start_notify(self, client: BleakClient) -> None:
        preferred = [normalize_uuid(uuid) for uuid in CHARACTERISTIC_UUIDS if uuid]
        preferred = [uuid for uuid in preferred if uuid]
        legacy = normalize_uuid(CHAR_UUID)
        if legacy and legacy not in preferred:
            preferred.insert(0, legacy)

        for uuid in preferred:
            try:
                await client.start_notify(uuid, self._on_notify)
                _LOGGER.info("Notify gestart op %s", uuid)
                return
            except Exception as err:
                _LOGGER.debug("Notify op %s niet beschikbaar: %s", uuid, err)

        service_collection = getattr(client, "services", None)
        if service_collection is None:
            discovered = "niet beschikbaar"
        else:
            services = getattr(service_collection, "services", service_collection)
            try:
                services = list(services)
            except TypeError:
                services = []

            if not services:
                discovered = "geen services ontdekt"
            else:
                service_details = []
                for service in services:
                    characteristics = []
                    for characteristic in getattr(service, "characteristics", []) or []:
                        properties = ",".join(
                            sorted(str(prop) for prop in getattr(characteristic, "properties", []) or [])
                        )
                        characteristics.append(
                            f"{getattr(characteristic, 'uuid', 'onbekend')} [{properties}]"
                        )
                    service_details.append(
                        f"{getattr(service, 'uuid', 'onbekend')}: "
                        f"{', '.join(characteristics) if characteristics else 'geen characteristics'}"
                    )
                discovered = "; ".join(service_details)

        raise RuntimeError(
            "Geen ondersteunde notify-characteristic gevonden voor CTEK Battery Sense "
            f"(geprobeerd: {', '.join(preferred)}; ontdekt GATT: {discovered})"
        )

    def _on_notify(self, _sender: int, data: bytearray) -> None:
        voltage = parse_data(data)
        if voltage is not None:
            self.voltage = round(voltage, 2)
            self.available = True
            self._notify_callbacks()

    def _on_disconnect(self, _client: BleakClient) -> None:
        _LOGGER.info("CTEK %s verbroken", self._address)
        self.available = False
        self._notify_callbacks()

    async def _authenticate(self, client: BleakClient) -> None:
        payload = build_sender_unlock_payload(self._sender_id)
        await client.write_gatt_char(
            UNLOCK_CHARACTERISTIC_UUID, payload, response=True
        )
        _LOGGER.debug("Sender ID-unlockpayload geschreven voor CTEK %s", self._address)

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

                await self._authenticate(client)
                await self._start_notify(client)

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
