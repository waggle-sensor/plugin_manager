import waggle.pipeline
import time
import sys
import .coresense


class CoresensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'coresense'
    plugin_version = '3'

    def run(self):
        if len(sys.argv) == 2:
            device = sys.argv[1]
        else:
            device = '/dev/waggle_coresense'

        with coresense.create_connection(device) as conn:
            while True:
                message = conn.recv()
                if message is not None:
                    self.send(sensor='frame', data=message.frame)
                time.sleep(5)


def register(name, man, mailbox_outgoing):
    CoresensePlugin(name, man, mailbox_outgoing).run()


if __name__ == '__main__':
    def callback(data):
        print(data)

    waggle.pipeline.run_standalone(CoresensePlugin, callback)
