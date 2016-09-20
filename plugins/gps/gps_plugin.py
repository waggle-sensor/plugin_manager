#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import datetime
import logging
import pynmea2
from serial import Serial
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        
        env = gps(name, man, mailbox_outgoing)
        
        env.run()

class gps(object):

    plugin_name = 'gps'
    plugin_version = '1'

    def __init__(self, name, man, mailbox_outgoing):
        self.name = name
        self.man = man
        self.outqueue = mailbox_outgoing
        

    def run(self):
        self.running = True
        while self.running:
            device = '/dev/gps_module'
            logger.debug("try to connect to device "+device)
            
            try:
              serial = Serial(device, timeout=180)
              while self.running:
                  try:
                      msg = serial.readline()
                  except Exception as e:
                      logger.error("(Inner loop) Error of type %s: %s" % (str(type(e)), str(e)))
                      msg = None
                      time.sleep(1)
                      break
              
                  if msg:    
                      self.handle_message(msg)
            except Exception as e:
                logger.error("(Outer loop) Error of type %s: %s" % (str(type(e)), str(e)))
                raise
            
            time.sleep(10)

    def stop(self):
        self.running = False

    def handle_message(self, message):
        logger.info(message)
        if "$GPGGA" in message:
          parsed_data = pynmea2.parse(message)
          self.handle_message_entry(parsed_data)

    def handle_message_entry(self, parsed_data):
        
        timestamp_date = time.strftime('%Y-%m-%d', datetime.datetime.now())
        timestamp_time = datetime.datetime.now().replace(
          hour=parsed_data.timestamp.hour,
          minute=parsed_data.timestamp.minute,
          second=parsed_data.timestamp.second)
        lat = float(parsed_data.lat)
        lat_deg = int(lat/100)
        lat_minutes = float(lat-lat_deg)
        lon = float(parsed_data.lon)
        lon_deg = int(lon/100)
        lon_minutes = float(lon-lon_deg)
        degree_sign = u'\N{DEGREE SIGN}'
        data_string = '%s%s%s\'%s %s%s%s\'%s' % (lat_deg, degree_sign, lat_minutes, parsed_data.lat_dir,\
                                                 lon_deg, degree_sign, lon_minutes, parsed_data.lon_dir)
        
        #self.outqueue.put([
        message = [
            str(timestamp_date).encode('iso-8859-1'),
            self.plugin_name.encode('iso-8859-1'),
            self.plugin_version.encode('iso-8859-1'),
            timestamp_time.encode('iso-8859-1'),
            data_string.encode('iso-8859-1'),
        ]
        #])
        print("Message: %s" % message)

    @property
    def running(self):
        return self.man[self.name] != 0

    @running.setter
    def running(self, state):
        self.man[self.name] = 1 if state else 0

if __name__ == "__main__":
  man = {}
  mail_outgoing = []
  plugin = gps('gps', man, mail_outgoing)
  plugin.run()
