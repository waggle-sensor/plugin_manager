#!/usr/bin/env python3
import logging
import pynmea2
from serial import Serial
import waggle.pipeline


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GPSPluign(waggle.pipeline.Plugin):

    plugin_name = 'gps'
    plugin_version = '1'

    def run(self):
        serial = Serial('/dev/gps_module', timeout=180)

        while True:
            line = serial.readline().decode()
            if "$GPGGA" in line:
                parsed_data = pynmea2.parse(line)
                # check for empty values
                try:
                    lat_degree = int(float(parsed_data.lat) / 100)
                    lat_minute = float(parsed_data.lat) - lat_degree*100
                    lon_degree = int(float(parsed_data.lon) / 100)
                    lon_minute = float(parsed_data.lon) - lon_degree*100
                    data_string = u'%s\u00b0%s\'%s,%s\u00b0%s\'%s,%s%s' % (lat_degree, lat_minute, parsed_data.lat_dir,
                                                                           lon_degree, lon_minute, parsed_data.lon_dir,
                                                                           parsed_data.altitude, parsed_data.altitude_units.lower())

                    self.send('gps', data_string)
                except:
                    pass


register = GPSPluign.register

if __name__ == '__main__':
    def callback(sensor, data):
        print(sensor)
        print(data)
        print()

    GPSPluign.run_standalone(callback)
