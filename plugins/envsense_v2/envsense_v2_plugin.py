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
        self.run(name, man)

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
        with coresense.create_connection('/dev/ttyACM0') as conn:
            while man[name]:
                message = conn.recv()

                # logger.info(message)

                for entry in message.entries:
                    formatted_values = ['{}:{}'.format(key, value)
                                        for key, value in entry.values]
                    self.send_values(entry.sensor, formatted_values)
