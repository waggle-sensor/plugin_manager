#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import logging
import datetime
import time
from base64 import b64encode
from .alphasense import Alphasense


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        plugin = AlphasensePlugin(name, man, mailbox_outgoing)
        plugin.run()


epoch = datetime.datetime.utcfromtimestamp(0)


def epoch_time(dt):
    return (dt - epoch).total_seconds() * 1000.0


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
                while True:
                    firmware_version = alphasense.get_firmware_version()
                    config_data = alphasense.get_config_data()
                    message = [
                        'firmware:' + firmware_version,
                        'config:' + b64encode(config_data),
                    ]

                    self.send_message('config', message)
                    logger.info('firmware / config sent')
                    time.sleep(1)

                    for _ in range(100):
                        histogram_data = alphasense.get_histogram_raw()
                        self.send_message('data', ['data:' + b64encode(histogram_data)])
                        logger.info('data sent')
                        time.sleep(10)
            finally:
                alphasense.close()

    def stop(self):
        self.running = False

    def send_message(self, ident, data):
        timestamp_utc = datetime.datetime.utcnow()
        timestamp_date = timestamp_utc.date()
        timestamp_epoch = int(float(timestamp_utc.strftime("%s.%f"))) * 1000

        message_data = [
            str(timestamp_date).encode('iso-8859-1'),
            'alphasense'.encode('iso-8859-1'),
            '1'.encode('iso-8859-1'),
            'default'.encode('iso-8859-1'),
            '%d' % timestamp_epoch,
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
