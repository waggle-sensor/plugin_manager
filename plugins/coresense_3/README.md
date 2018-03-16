## Coresense version 3.x plugin

The plugin is designed to connect to the attached Metsense, receive Waggle frames from the Metsense, and ship received frames to Beehive via RabbitMQ. The plugin is driven by `systemd` service and runs when the system is in normal operaion mode. This plugin is compatible with Metsense firmware version 3.x and _not_ compatible with any other Metsense firmware versions, e.g., version 4.x.

### Logical flow
```
               |START|
                  +
                  +
               |Sensor?| -- No -- |END|
                  +
                 Yes
                  +
               |Connect?| -- No -- |Print Error| -- |END|
                  +
                 Yes
----------------->+<-------------------------------------------
|            |Receive data?| -- No ---                        |
|                 +                  |                        |
|                Yes                 |                        |
|                 +                  |                        No
|---- No -- |Receive packet?|        |                        |
|                 +                  -- |Increment FC| -- |FC >= 10?| -- Yes -- |END|
|                Yes                 |
|                 +                  |
|            |Check CRC|             |
|                 +                  |
|                 +                  |
|           |Correct CRC?| -- No ----- 
|                 +
|                Yes
|                 +
|           |Send packet|
|                 +
|                 +
-------------------
```

The plugin expects to receive a Waggle frame from the connected serial port within 29 seconds after it finishes its initialization. The failure count (FC) is increased every 3 seconds when no Waggle frame is received or when incorrect CRC is received. When FC is equal or greater than 10, the plugin raises an exception and terminates itself. However, systemd service will re-spawn the plugin in 15 seconds after termination.

All log messages that the plugin publishes are accessible from journal system,
```
# Print out log messages for the last 1 hour
journalctl -u waggle-plugin-coresense --since=-1h
```

### Troubleshooting

1) No `Received frame` in the log
