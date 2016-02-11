# -*- coding: utf-8 -*-
import os
import time
import datetime
from coresense import coresense_reader


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

        self.outqueue.put([
            str(timestamp_date),
            self.plugin_name,
            self.plugin_version,
            'default',
            str(timestamp_epoch),
            sensor_name,
            'meta.txt',
            sensor_values,
        ])

    def run(self, name, man):
        while man[name]:
            try:
                for ts, ident, values in coresense_reader('/dev/ttyACM0'):
                    self.send_values(ident, ['{}:{}'.format(name, value)
                                             for name, value in values])
            except:
                pass


if __name__ == '__main__':
    for ts, ident, values in coresense_reader('/dev/ttyACM0'):
        print('@ {} {}'.format(ident, ts))
        for name, value in values:
            print('- {}: {}'.format(name, value))
        print('')
