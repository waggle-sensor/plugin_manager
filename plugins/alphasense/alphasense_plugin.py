#!/usr/bin/env python3
import logging
import time
import waggle.pipeline
import sys
import os
from alphasense import Alphasense
from contextlib import closing


device = os.environ.get('ALPHASENSE_DEVICE', '/dev/alphasense')

class AlphasensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'alphasense'
    plugin_version = '1'

    def run(self):
        print('Connecting to device: {}'.format(device), flush=True)

        with closing(Alphasense(device)) as alphasense:
            print('Connected to device: {}'.format(device), flush=True)

            print('Setting OPN-N2 fan power.', flush=True)
            alphasense.set_fan_power(255)
            time.sleep(3)

            print('Setting OPN-N2 laser power.', flush=True)
            alphasense.set_laser_power(190)
            time.sleep(3)

            print('Powering OPN-N2 on.', flush=True)
            alphasense.power_on()
            time.sleep(3)

            while True:
                firmware = alphasense.get_firmware_version()
                config = alphasense.get_config_data_raw()

                if firmware.startswith(b'\xf3\xf3\xf3\xf3'):
                    raise RuntimeError('not ready')

                if config.startswith(b'\xf3\xf3\xf3\xf3'):
                    raise RuntimeError('not ready')

                self.send('firmware', firmware)
                self.send('config', config)

                for _ in range(100):
                    histogram = alphasense.get_histogram_raw()

                    if histogram.startswith(b'\xf3\xf3\xf3\xf3'):
                        raise RuntimeError('not ready')

                    self.send('histogram', histogram)
                    time.sleep(10)

plugin = AlphasensePlugin.defaultConfig()
plugin.run()
