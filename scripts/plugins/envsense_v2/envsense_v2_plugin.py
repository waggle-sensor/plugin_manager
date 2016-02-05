import time
import datetime
# from multiprocessing import Queue


class register(object):

    plugin_name = 'Dummy'
    plugin_version = '1'

    def __init__(self, name, man, mailbox_outgoing):
        man[name] = 1
        self.outqueue = mailbox_outgoing
        self.run()

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

    def run(self):
        while True:
            self.send_values('NONSENSE', ['Temperature', '-43K',
                                          'Pressure', '123456789 Pa'])
            time.sleep(30)
