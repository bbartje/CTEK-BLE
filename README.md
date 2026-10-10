# CTEK BLE Integration

Home Assistant integration for CTEK Battery Sense BLE sensors.

## Features
- Voltage
- Temperature
- Estimated charging status (derived from voltage)
- Estimated battery state (derived from voltage)

## Important protocol note

BLE advertisements are only useful for discovery. Reliably reading the CTEK Battery Sense measurements requires an active GATT connection. This repository therefore keeps the Home Assistant integration architecture: it authenticates to the device and reads live data from the GATT service instead of trusting passive scan payloads.

The reverse-engineered service and characteristic UUIDs are:
- service: `812ca8ed-a177-4d74-aefa-70098c5416af`
- unlock/write: `a1d67c01-fe3f-01bf-7d49-7dbdc43b02a6`
- voltage notify: `a337b4eb-2544-4f94-87c9-f7732e5fe250`
- temperature read: `b5634099-97c4-4f37-adf3-771246e77754`
- optional range attribute seen in the app flow: `418d1817-f516-45f1-ab64-433ae596613d`

The app uses the unlock handshake with the device's 16-character Sender ID before live measurement data is requested. The temperature is a signed byte divided by 2; the voltage payload is a 3-byte record with little-endian voltage / 2048 and a signed auxiliary byte.

## Installation
1. In HACS, add `bbartje/CTEK-BLE` as a custom integration repository.
2. Install or update **CTEK BLE Battery Sensors**.
3. Restart Home Assistant, then add **CTEK BLE Battery Sensors** from Settings > Devices & services.

This release is still not validated on physical CTEK Battery Sense hardware. Please report the Home Assistant version, Bluetooth adapter or proxy model, integration logs, and whether the device appears during setup.

## Bluetooth proxy troubleshooting

The first setup asks for the 16-character Sender ID printed on the device sticker. The integration uses it for the device's GATT unlock handshake before subscribing to notifications and reading temperature values. Existing entries can set or correct the ID in the integration options.

If the CTEK only accepts a connection briefly after a power cycle, interrupt its power briefly immediately before adding it or saving the Sender ID, then retry at once. This is a troubleshooting step based on observed device behavior; it has not been established whether every reconnect requires a power cycle.

Voltage notifications use the CTEK GATT characteristic. Temperature is read from its separate GATT characteristic every 30 seconds. Both measurements require an active Bluetooth connection; the advertisements alone do not contain them. Charging and battery-state sensors are estimates based on voltage thresholds, not status fields reported by the device.

When using an ESPHome Bluetooth proxy, make sure it is online and the CTEK device is visible to Home Assistant through the Bluetooth integration. If notify setup fails, the integration log now includes the GATT service and characteristic UUIDs and their properties. Include that complete message, the ESPHome device model and version, and the Home Assistant version when reporting the issue.

## Reference gateway

A separate active BLE ESP32 gateway prototype exists as a reference for the bridge model and protocol work:
- https://github.com/bbartje/ctek-ble-ESP32-gateway/tree/v0.1.0-beta.1

This repository keeps the Home Assistant custom integration architecture and does not merge the ESP32 firmware directly. The gateway project is a reference implementation for the bridge design; it is still a prerelease and has not been validated on physical CTEK hardware here.

# CTEK BLE

![logo](logo.png)
