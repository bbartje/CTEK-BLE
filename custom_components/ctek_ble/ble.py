import asyncio
from bleak import BleakClient, BleakScanner
from .const import SERVICE_UUID, CHAR_UUID

class CTEKDevice:
    def __init__(self, address, name):
        self.address = address
        self.name = name or address
        self.voltage = None
        self.temperature = None
        self._callbacks = []

    def add_callback(self, cb):
        self._callbacks.append(cb)

    def _notify(self):
        for cb in self._callbacks:
            cb()

    def _parse(self, data: bytearray):
        if len(data) < 3:
            return
        self.voltage = int.from_bytes(data[0:2], "little") / 2048
        self.temperature = data[2] - 17
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
        if SERVICE_UUID.lower() in [s.lower() for s in d.metadata.get("uuids", [])]:
            result.append(CTEKDevice(d.address, d.name))

    return result
