#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import logging
import time
from base64 import b64encode
from .alphasense import Alphasense


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        plugin = AlphasensePlugin(name, man, mailbox_outgoing)
        plugin.run()

class AlphasensePlugin(object):

    plugin_name = 'alphasense'
    plugin_version = '1'

    def __init__(self, name, man, mailbox_outgoing):
        self.name = name
        self.man = man
        self.outqueue = mailbox_outgoing

    def run(self):
        self.running = True

        while self.running:
            alphasense = Alphasense('/dev/alphasense')
            time.sleep(1)
            logger.info('alphasense init')

            alphasense.power_on()
            time.sleep(1)
            logger.info('alphasense on')

            try:
                while self.running:
                    firmware_version = alphasense.get_firmware_version()
                    config_data = alphasense.get_config_data_raw()
                    message = [
                        'firmware:'.encode('iso-8859-1') + firmware_version,
                        'config:'.encode('iso-8859-1') + str(config_data).encode('iso-8859-1'),
                    ]

                    self.send_message('config', message)
                    logger.info('firmware / config sent')
                    time.sleep(1)

                    for _ in range(100):
                        histogram_data = alphasense.get_histogram_raw()
                        self.send_message('data', ['data:'.encode('iso-8859-1') + b64encode(histogram_data)])
                        logger.info('data sent')
                        time.sleep(10)
            finally:
                alphasense.close()

    def stop(self):
        self.running = False

    def send_message(self, ident, data):
        timestamp_utc = int(time.time())
        timestamp_date  = time.strftime('%Y-%m-%d', time.gmtime(timestamp_utc))
        timestamp_epoch = timestamp_utc * 1000

        message_data = [
            str(timestamp_date).encode('iso-8859-1'),
            'alphasense'.encode('iso-8859-1'),
            '1'.encode('iso-8859-1'),
            'default'.encode('iso-8859-1'),
            '%d' % (timestamp_epoch),
            ident.encode('iso-8859-1'),
            'base64'.encode('iso-8859-1'),
            data,
        ]

        self.outqueue.put(message_data)

    @property
    def running(self):
        return self.man[self.name] != 0

    @running.setter
    def running(self, state):
        self.man[self.name] = 1 if state else 0
