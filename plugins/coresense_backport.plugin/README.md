<!--
waggle_topic=/plugins_and_code
-->

# Coresense 4.1 Plugin

## Behavior of the plugin

The plugin actively sends _request_ commands to the Metsense board and waits for _response_. It uses Waggle protocol version 5, so the counterpart of the plugin should be able to user the same protocol to decode.

## Printing values

The plugin supports _human readable form_ feature that allows users to see the sensor values conveniently. Running the plugin with the option `--hrf` will trigger this feature. Note that proper version (0.23.0 or greater) of *PyWaggle* must be installed in the machine in order to convert the values into the form.

## Default sensor configuration

The plugin refers to the configuration file to determine what to request. The file is stored at `/wagglerw/waggle/sensor_table.conf`. If users wish to change request interval or add/remove sensors, modify the configuration file and re-run the plugin. Below is the default sensor configuration,

```
sensor_table = {
        'MetMAC': { 'sensor_id': 0x00, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'TMP112': { 'sensor_id': 0x01, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'HTU21D': { 'sensor_id': 0x02, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'HIH4030': { 'sensor_id': 0x03, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'BMP180': { 'sensor_id': 0x04, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'PR103J2': { 'sensor_id': 0x05, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'TSL250RDMS': { 'sensor_id': 0x06, 'function_call': 'sensor_read', 'interval': 25 },  #o, light, return raw
        'MMA8452Q': { 'sensor_id': 0x07, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'SPV1840LR5H-B': { 'sensor_id': 0x08, 'function_call': 'sensor_read', 'interval': 25 },  #o 63 readings
        'TSYS01': { 'sensor_id': 0x09, 'function_call': 'sensor_read', 'interval': 25 },  #o

        'HMC5883L': { 'sensor_id': 0x0A, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'HIH6130': { 'sensor_id': 0x0B, 'function_call': 'sensor_read', 'interval': 25 },  #o
        'APDS_9006_020': { 'sensor_id':0x0C, 'function_call': 'sensor_read', 'interval': 25 },  #o, light, return raw
        'TSL260': { 'sensor_id': 0x0D, 'function_call': 'sensor_read', 'interval': 25 },  #o, light, return raw
        'TSL250RDLS': { 'sensor_id': 0x0E, 'function_call': 'sensor_read', 'interval': 25 },  #o, light, return raw
        'MLX75305': { 'sensor_id': 0x0F, 'function_call': 'sensor_read', 'interval': 25 },  #o, light, return raw
        'ML8511': { 'sensor_id': 0x10, 'function_call': 'sensor_read', 'interval': 25 },  #o, light, return raw
        'TMP421': { 'sensor_id': 0x13, 'function_call': 'sensor_read', 'interval': 25 },  #o

        # For BUS calls
        # 'BusTMP112': { 'function_call': 'bus_read', 'bus_type': 0x00, 'bus_address': 0x48, 'params': [0x00], 'interval': 1 },
        # 'BusHTU21D': { 'function_call': 'bus_read', 'bus_type': 0x00, 'bus_address': 0x40, 'params': [0xF3, 0xF5], 'interval': 1 },
        # 'BusChemsense': { 'function_call': 'bus_read', 'bus_type': 0x02, 'bus_address': 0x03, 'params': [], 'interval': 1 },

        # 'ChemConfig': { 'sensor_id': 0x16, 'function_call': 'sensor_read', 'interval': 1 },
        'Chemsense': { 'sensor_id': 0x2A, 'function_call': 'sensor_read', 'interval': 25 },

        # 'AlphaON': { 'sensor_id': 0x2B, 'function_call': 'sensor_read', 'interval': 1 },
        'AlphaFirmware': { 'sensor_id': 0x30, 'function_call': 'sensor_read', 'interval': 25 },
        'AlphaSerial': { 'sensor_id': 0x29, 'function_call': 'sensor_read', 'interval': 25 },
        'AlphaHisto': { 'sensor_id': 0x28, 'function_call': 'sensor_read', 'interval': 25 },
        'AlphaConfig': { 'sensor_id': 0x31, 'function_call': 'sensor_read', 'interval': 1 },
    }
```

Note that there are some *ONE-TIME* commands: `AlphaON`, `AlphaConfig`, and `ChemConfig` -- those are designed to be called only when necessary.
