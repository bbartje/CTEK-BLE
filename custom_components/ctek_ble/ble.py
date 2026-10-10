import asyncio
from bleak import BleakClient, BleakScanner
from .const import SERVICE_UUIDS, CHAR_UUID, is_ctek_device
from .protocol import parse_data

class CTEKDevice:
    def __init__(self, address, name):
        self.address = address
        self.name = name or address
        self.voltage = None
        self._callbacks = []

    def add_callback(self, cb):
        self._callbacks.append(cb)

    def _notify(self):
        for cb in self._callbacks:
            cb()

    def _parse(self, data: bytearray):
        voltage = parse_data(data)
        if voltage is None:
            return
        self.voltage = voltage
        self._notify()

    async def run(self):
        while True:
            try:
                async with BleakClient(self.address) as client:
                    await client.start_notify(CHAR_UUID, self._handler)
                    while True:
                        await asyncio.sleep(60)
            except Exception:
                await asyncio.sleep(5)

    def _handler(self, sender, data):
        self._parse(data)


async def discover_devices():
    devices = await BleakScanner.discover()
    result = []

    for d in devices:
        details = getattr(d, "details", {}) or {}
        metadata = getattr(d, "metadata", {}) or {}
        service_uuids = [
            str(uuid)
            for uuid in (details.get("uuids") or metadata.get("uuids", []))
        ]
        if is_ctek_device(d.name, service_uuids):
            result.append(CTEKDevice(d.address, d.name))

    return result
