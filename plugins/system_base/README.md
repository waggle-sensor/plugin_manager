# System base plugin

This plugin monitors system information and activities such as boot and shutdown, and reports the information to the server. It also reports the current status of waggle services and whitelist of plugins.

## Reporting system information

Here are the information the plugin monitors and reports...

* Disk usage (total, used, and free in byte)
* Host name (node_id and either 'SD' or 'eMMC')
* Reboot log (last three reboot history)
* Shutdown log (last four shutdown history)
* CPU temperature (in degree Celsius)

We can determine whether the last boot happend by sudden event (e.g., power down) or by polite reboot command. If the time of the latest reboot matches the time of the lastest shutdown log, it was a polite reboot, otherwise it was a sudden reboot.

## Reporting waggle information

The plugin also reports status of waggle services.

* Current status of waggle services
* Whitelist plugins

## Auto-run plugins

This plugin reads autostartlist.txt file located under 'plugins' folder in order to get the list of autostart-enabled plugins. And then, this plugin periodically checks if any of the sensors is physically connected such that once a sensor is connected it can send 'start' command to plugin_manager to start the plugin for the connected board.

However, this plugin does not stop or kill a plugin when the sensor board is physically detached because it would be difficult to reason why the board was disconnected.