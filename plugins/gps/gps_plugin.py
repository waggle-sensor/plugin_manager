#!/usr/bin/env python3
import logging
import os.path
import pynmea2
from serial import Serial
import waggle.pipeline
import time


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)
logging.basicConfig(level=logging.WARN)

device = os.environ.get('GPS_DEVICE', '/dev/gps_module')


class GPSPlugin(waggle.pipeline.Plugin):
    plugin_name = 'gps'
    plugin_version = '1'

    def run(self):
        serial = Serial(device, timeout=180)

        while True:
            line = serial.readline().decode()
            if "$GPGGA" in line:
                parsed_data = pynmea2.parse(line)

                if not parsed_data.lat:
                    logger.warn('gps could not lock')
                    time.sleep(10)
                    continue

                try:
                    lat_degree = int(float(parsed_data.lat) / 100)
                    lat_minute = float(parsed_data.lat) - lat_degree*100
                    lon_degree = int(float(parsed_data.lon) / 100)
                    lon_minute = float(parsed_data.lon) - lon_degree*100
                    data_string = '%s*%s\'%s,%s*%s\'%s,%s%s' % (lat_degree, lat_minute, parsed_data.lat_dir,
                                                                           lon_degree, lon_minute, parsed_data.lon_dir,
                                                                           parsed_data.altitude, parsed_data.altitude_units.lower())
                except Exception as e:
                    logger.exception(e)
                    time.sleep(10)
                    continue
                logger.debug(data_string)
                self.send('gps', data_string)
                time.sleep(10)

if os.path.exists(device):
    plugin = GPSPlugin.defaultConfig()
    plugin.run()
else:
    exit(1)
