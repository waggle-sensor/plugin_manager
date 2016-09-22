#!/usr/bin/env python3
import waggle.pipeline
import time
import random


class ExamplePlugin(waggle.pipeline.Plugin):

    plugin_name = 'example'
    plugin_version = '1'

    def run(self):
        while True:
            self.send('greeting',
                      'hello!')
            self.send('temperature',
                      str(20.00 + random.random() - 0.5))
            time.sleep(10)


def register(name, man, mailbox_outgoing):
    plugin = ExamplePlugin(name, man, mailbox_outgoing)
    plugin.run()

if __name__ == '__main__':
    def callback(data):
        print(data)

    waggle.pipeline.run_standalone(ExamplePlugin, callback)
