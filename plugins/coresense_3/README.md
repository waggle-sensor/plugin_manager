## Coresense version 3.x plugin

The plugin is designed to connect to the attached Metsense, receive Waggle frames from the Metsense, and ship received frames to Beehive via RabbitMQ. The plugin is driven by `systemd` service and runs when the system is in normal operaion mode. This plugin is compatible with Metsense firmware version 3.x and _not_ compatible with any other Metsense firmware versions, e.g., version 4.x.

