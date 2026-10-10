# CTEK BLE Integration

Home Assistant integration for CTEK Battery Sense BLE sensors.

## Features
- Voltage
- Temperature
- Estimated charging status (derived from voltage)
- Estimated battery state (derived from voltage)

## Installation
1. In HACS, add `bbartje/CTEK-BLE` as a custom integration repository.
2. Install or update **CTEK BLE Battery Sensors**.
3. Restart Home Assistant, then add **CTEK BLE Battery Sensors** from Settings > Devices & services.

This test release has not yet been verified against a live Battery Sense module. Please report the Home Assistant version, Bluetooth adapter or proxy model, integration logs, and whether the device appears during setup.

## Bluetooth proxy troubleshooting

The first setup asks for the 16-character Sender ID printed on the device sticker. The integration uses it for the device's GATT unlock handshake before subscribing to notifications; it is not used to decode the voltage payload. Existing entries can set or correct the ID in the integration options.

If the CTEK only accepts a connection briefly after a power cycle, interrupt its power briefly immediately before adding it or saving the Sender ID, then retry at once. This is a troubleshooting step based on observed device behavior; it has not been established whether every reconnect requires a power cycle.

Voltage notifications use the CTEK GATT characteristic. Temperature is read from its separate GATT characteristic every 30 seconds. Both measurements require an active Bluetooth connection; the advertisements alone do not contain them. Charging and battery-state sensors are estimates based on voltage thresholds, not status fields reported by the device.

When using an ESPHome Bluetooth proxy, make sure it is online and the CTEK device is visible to Home Assistant through the Bluetooth integration. If notify setup fails, the integration log now includes the GATT service and characteristic UUIDs and their properties. Include that complete message, the ESPHome device model and version, and the Home Assistant version when reporting the issue.

# CTEK BLE

![logo](logo.png)
