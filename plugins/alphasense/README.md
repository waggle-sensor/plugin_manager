<!--
waggle_topic=/plugins_and_code
-->

# Alphasense Plugin

*Note: This plugin is deprecated. Alphasense logic has been integrated into the Coresense 4.*

The Alphasense is allowed to

# Histogram

The layout of the histogram is as follows in this order:

* bins: 16 x 16-bit unsigned integer
* mtof: 4 x 8-bit unsigned integer
* sample flow rate: single precision float
* temperature / pressure: single precision float
* sampling rate: single precision float
* checksum: 16-bit unsigned integer (sum of bins)
* pm 1: single precision float
* pm 2.5: single precision float
* pm 10: single precision float
