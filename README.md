# CTEK BLE Integration

Home Assistant integration for CTEK Battery Sense BLE sensors.

## Features
- Voltage
- Charging status
- Battery state

## Installation
1. In HACS, add `bbartje/CTEK-BLE` as a custom integration repository.
2. Install or update **CTEK BLE Battery Sensors**.
3. Restart Home Assistant, then add **CTEK BLE Battery Sensors** from Settings > Devices & services.

This test release has not yet been verified against a live Battery Sense module. Please report the Home Assistant version, Bluetooth adapter or proxy model, integration logs, and whether the device appears during setup.

## Bluetooth proxy troubleshooting

The first setup asks for the 16-character Sender ID printed on the device sticker. The integration uses it for the device's GATT unlock handshake before subscribing to notifications; it is not used to decode the voltage payload. Existing entries can set or correct the ID in the integration options.

When using an ESPHome Bluetooth proxy, make sure it is online and the CTEK device is visible to Home Assistant through the Bluetooth integration. If notify setup fails, the integration log now includes the GATT service and characteristic UUIDs and their properties. Include that complete message, the ESPHome device model and version, and the Home Assistant version when reporting the issue.

# CTEK BLE

![logo](logo.png)
