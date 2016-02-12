# -*- coding: utf-8 -*-
import os, time, datetime, logging
from coresense import coresense_reader

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
        
        print str(message)
        self.outqueue.put(message)

    def run(self, name, man):
       
        while man[name]:
            try:
                for ts, ident, values in coresense_reader('/dev/ttyACM0'):
                    if not man[name]:
                        break
                    try:    
                        self.send_values(ident, ['{}:{}'.format(key, value)
                                             for key, value in values])
                    except Exception as e:
                        logger.error('error(send_values): %s' % (str(e)))
            except Exception as e:
                logger.error('error(coresense_reader): %s' % (str(e)))
                


if __name__ == '__main__':
    for ts, ident, values in coresense_reader('/dev/ttyACM0'):
        print('@ {} {}'.format(ident, ts))
        for name, value in values:
            print('- {}: {}'.format(name, value))
        print('')
