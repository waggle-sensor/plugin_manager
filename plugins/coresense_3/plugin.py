import waggle.pipeline
import time
import sys
from coresense import create_connection


class CoresensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'coresense'
    plugin_version = '3'

    def run(self):
        if len(sys.argv) == 2:
            device = sys.argv[1]
        else:
            device = '/dev/waggle_coresense'

        with create_connection(device) as conn:
            while True:
                message = conn.recv()
                if message is not None:
                    self.send(sensor='frame', data=message.frame)
                time.sleep(5)


register = CoresensePlugin.register

if __name__ == '__main__':
    def callback(sensor, data):
        print(sensor)
        print(data)
        print()

    CoresensePlugin.run_standalone(callback)
