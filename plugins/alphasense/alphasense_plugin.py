#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import waggle.pipeline
import time
import sys
import os
from alphasense import Alphasense
from contextlib import closing


device = os.environ.get('ALPHASENSE_DEVICE', '/dev/alphasense')

class AlphasensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'alphasense'
    plugin_version = '1'

    def run(self):
        # don't bother trying to connect to the alphasense if it doesn't exist
        while not os.path.islink(device) :
          time.sleep(10)

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

if os.path.exists(device):
    plugin = AlphasensePlugin.defaultConfig()
    plugin.run()
else:
    exit(1
