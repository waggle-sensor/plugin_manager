#!/usr/bin/env python3
import waggle.pipeline
import time
from . import coresense


class CoresensePlugin(waggle.pipeline.Plugin):

    plugin_name = 'coresense'
    plugin_version = '3'

    def run(self):
        with coresense.create_connection('/dev/waggle_coresense') as conn:
            while True:
                message = conn.recv()
                if message is not None:
                    self.send(sensor='frame', data=message.frame)
                time.sleep(10)


class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        CoresensePlugin(name, man, mailbox_outgoing).run()
