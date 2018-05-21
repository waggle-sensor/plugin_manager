<!--
waggle_topic=Waggle/Node/Plugins
-->

# Waggle Plugin Manager

_WARNING: this document is __outdated__ and needs update_

Plugins provide the functionality to read and preprocess raw sensor values from attached sensors (e.g. attached via USB or GPIOs) locally on the compute nodes.

## Installation

```bash
mkdir -p /usr/lib/waggle
cd /usr/lib/waggle
git clone https://github.com/waggle-sensor/waggle_image.git
git clone --recursive https://github.com/waggle-sensor/plugin_manager.git
cd plugin_manager
./configure
```

## Monitoring
The plugin manager will be executed by supervised. To see if the plugin manager is running:
```
supervisorctl status
```

The log files can be viewed like this:
```
tail -f /var/log/waggle/plugin_manager.log
```

## Managing plugins
```
cd /usr/lib/waggle/plugin_manager
./waggle_plugins.py
```
This script can be used to list, start and stop plugins and the command line. It can also be used to view the messages that are beeing send by the plugins to the nodecontroller.

## Script details

* [Message handler](/lib/msg_handler.py)

* [Plugin manager](plugin_manager.py)

* [Waggle plugins](waggle-plugins.py)
