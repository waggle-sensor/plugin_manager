<!--
waggle_topic=/plugins_and_code
-->

# Coresense Backport Plugin

This plugin backports support for the new Waggle protocol to the old coresense 4
configuration and firmware.

## Usage

```
./plugin_bin/plugin_node
```

## Flags

```
--debug - Only do local fetching and printing of sensorgrams. Intended for testing.
--device /dev/some.tty - Override default /dev/waggle_coresense device path.
```
