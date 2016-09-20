#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import datetime
import logging
import pynmea2
from serial import Serial
import time
import queue

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        
        env = gps(name, man, mailbox_outgoing)
        
        env.run()

class gps(object):

    plugin_name = 'spec_dsdk'
    plugin_version = '1'

    def __init__(self, name, man, mailbox_outgoing):
        self.name = name
        self.man = man
        self.outqueue = mailbox_outgoing
        

    def run(self):
        self.running = True
        while self.running:
            device = '/dev/spec_module'
            logger.debug("try to connect to device "+device)
            
            try:
              serial = Serial(device, timeout=180)
              while self.running:
                  try:
                      serial.write(b' ')
                      time.sleep(1)
                      data = serial.readline()
                  except Exception as e:
                      logger.error("(Inner loop) Error of type %s: %s" % (str(type(e)), str(e)))
                      data = None
                      time.sleep(1)
                      break
              
                  if data:    
                      self.handle_data(data)
            except Exception as e:
                logger.error("(Outer loop) Error of type %s: %s" % (str(type(e)), str(e)))
                raise
            
            time.sleep(10)

    def stop(self):
        self.running = False

    def handle_data(self, data):
        logger.info(data)
        timestamp_now = datetime.datetime.now()
        timestamp_date = timestamp_now.strftime('%Y-%m-%d')
        timestamp_time = timestamp_now.strftime('%s')
        """
        [Unique Sensor Serial Number, Gas Concentration (ppb), Temperature (°C),
        Relative Humidity (%), Gas Sensor Measurement (ADC counts), Temperature Sensor Measurement
        (ADC counts), Relative Humidity Sensor Measurement (ADC counts), Days Elapsed, Hours Elapsed,
        Minutes Elapsed, Seconds Elapsed]

        072216010211, 38604, 26, 42, 17411, 27448, 25582, 00, 00, 00, 38
        """
        """
        df = pd.DataFrame(data, columns=['Unique Sensor Serial Number', 'Gas Concentration (ppb)', 'Temperature (°C)', 'Relative Humidity (%)',
                                         'Gas Sensor Measurement (ADC counts)', 'Temperature Sensor Measurement (ADC counts)',
                                         'Relative Humidity Sensor Measurement (ADC counts)', 'Days Elapsed, Hours Elapsed',
                                         'Minutes Elapsed', 'Seconds Elapsed'])

        """
        
        """
        date string         'YYYY-MM-DD'
        plugin name         'myplugin'
        plugin version      '1'
        plugin instance     'default'
        timestamp epoch     'YYYY-MM-DD HH:MM:DD'
        sensor name         'SENS123'
        meta                'meta.txt'
        data                'blob' 
        """
        message = [
            timestamp_date.encode('iso-8859-1'),
            self.plugin_name.encode('iso-8859-1'),
            self.plugin_version.encode('iso-8859-1'),
            'default',
            timestamp_time.encode('iso-8859-1'),
            'CO',
            '',
            str(data).encode('iso-8859-1'),
        ]
        print("Message: %s" % message)
        self.outqueue.put(message)

    @property
    def running(self):
        return self.man[self.name] != 0

    @running.setter
    def running(self, state):
        self.man[self.name] = 1 if state else 0

if __name__ == "__main__":
  man = {}
  mail_outgoing = queue.Queue()
  plugin = gps('gps', man, mail_outgoing)
  plugin.run()
