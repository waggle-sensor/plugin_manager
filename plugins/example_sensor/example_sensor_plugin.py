#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
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
    plugin = ExamplePlugin()
    plugin.add_handler(waggle.pipeline.LogHandler())
    plugin.run()
