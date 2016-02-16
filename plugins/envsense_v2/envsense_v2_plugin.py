# -*- coding: utf-8 -*-
import logging
import coresense
import datetime


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class register(object):

    plugin_name = 'envsense'
    plugin_version = '2'

    def __init__(self, name, man, mailbox_outgoing):
        man[name] = 1
        self.outqueue = mailbox_outgoing

        # self.connection = coresense.Connection('/dev/ttyACM0')
        self.connection = coresense.Connection('/dev/tty.usbmodem1421')

        try:
            self.run(name, man)
        except Exception as e:
            logger.error('error(coresense_reader): {}'.format(e))
        finally:
            self.connection.close()

    def send_values(self, sensor_name, sensor_values):
        timestamp_utc = datetime.datetime.utcnow()
        timestamp_date = timestamp_utc.date()
        timestamp_epoch = int(float(timestamp_utc.strftime("%s.%f")) * 1000)

        message = [
            str(timestamp_date),
            self.plugin_name,
            self.plugin_version,
            'default',
            str(timestamp_epoch),
            sensor_name,
            'meta.txt',
            sensor_values,
        ]

        self.outqueue.put(message)

    def run(self, name, man):
        while man[name]:
            message = self.connection.recv()

            logger.info(message)

            for entry in message.entries:
                formatted_values = ['{}:{}'.format(key, value)
                                    for key, value in entry.values]
                self.send_values(entry.sensor, formatted_values)
                # logger.info(entry)
