#!/usr/bin/env python3
import logging
import pynmea2
from serial import Serial
import waggle.pipeline
import time


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GPSPlugin(waggle.pipeline.Plugin):

    plugin_name = 'gps'
    plugin_version = '1'

    def run(self):
        serial = Serial('/dev/gps_module', timeout=180)

        while True:
            line = serial.readline().decode()
            if "$GPGGA" in line:
                parsed_data = pynmea2.parse(line)

                if not parsed_data.lat:
                    logging.warn('gps could not lock')
                    continue

                try:
                    lat_degree = int(float(parsed_data.lat) / 100)
                    lat_minute = float(parsed_data.lat) - lat_degree*100
                    lon_degree = int(float(parsed_data.lon) / 100)
                    lon_minute = float(parsed_data.lon) - lon_degree*100
                    data_string = '%s*%s\'%s,%s*%s\'%s,%s%s' % (lat_degree, lat_minute, parsed_data.lat_dir,
                                                                           lon_degree, lon_minute, parsed_data.lon_dir,
                                                                           parsed_data.altitude, parsed_data.altitude_units.lower())

                    self.send('gps', data_string)
                    time.sleep(10)
                except Exception as e:
                    logging.exception(e)


register = GPSPlugin.register

if __name__ == '__main__':
    plugin = GPSPlugin.defaultConfig()
    plugin.run()
