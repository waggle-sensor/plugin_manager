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


register = ExamplePlugin.register

if __name__ == '__main__':
    def callback(sensor, data):
        print(sensor)
        print(data)
        print()

    ExamplePlugin.run_standalone(callback)
