import waggle.pipeline
import time
import coresense


class CoresensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'coresense'
    plugin_version = '3'

    def run(self):
        with coresense.create_connection('/dev/tty.usbmodem1421') as conn:
            while True:
                message = conn.recv()
                if message is not None:
                    self.send(sensor='frame', data=message.frame)
                time.sleep(5)


class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        CoresensePlugin(name, man, mailbox_outgoing).run()


if __name__ == '__main__':
    from multiprocessing import Process, Queue

    q = Queue()
    p = Process(target=register, args=('', '', q))
    p.start()

    while True:
        print(q.get())
        print()
