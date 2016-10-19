#!/usr/bin/env python3
import logging
import time
import waggle.pipeline
from contextlib import closing
import sys

try:
    from .alphasense import Alphasense
except:
    from alphasense import Alphasense


logger = logging.getLogger('alphasense')
logger.setLevel(logging.DEBUG)


class AlphasensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'alphasense'
    plugin_version = '1'

    def run(self):
        if len(sys.argv) == 2:
            device = sys.argv[1]
        else:
            device = '/dev/alphasense'

        with closing(Alphasense(device)) as alphasense:
            logger.info('setting alphasense fan power')
            alphasense.set_fan_power(255)
            time.sleep(3)

            logger.info('setting alphasense laser power')
            alphasense.set_laser_power(190)
            time.sleep(3)

            logger.info('powering alphasense on')
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


register = AlphasensePlugin.register

if __name__ == '__main__':
    plugin = AlphasensePlugin()
    plugin.add_handler(waggle.pipeline.LogHandler())
    plugin.run()
