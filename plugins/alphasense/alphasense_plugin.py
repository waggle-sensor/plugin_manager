#!/usr/bin/env python3
import logging
import time
import waggle.pipeline
from contextlib import closing
import sys
from .alphasense import Alphasense


logger = logging.getLogger(__name__)
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
            time.sleep(1)

            logger.info('setting alphasense laser power')
            alphasense.set_laser_power(190)
            time.sleep(1)

            logger.info('powering alphasense on')
            alphasense.power_on()
            time.sleep(1)

            logger.info('alphasense ready')

            while True:
                self.send('firmware',
                          alphasense.get_firmware_version())

                self.send('config',
                          alphasense.get_config_data_raw())

                for _ in range(100):
                    self.send('histogram',
                              alphasense.get_histogram_raw())
                    time.sleep(10)


register = AlphasensePlugin.register

if __name__ == '__main__':
    def callback(sensor, data):
        print(sensor)
        print(data)
        print()

    AlphasensePlugin.run_standalone(callback)
