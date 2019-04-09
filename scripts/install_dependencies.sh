#!/bin/bash
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license


# python2
apt install python-psutil
pip install pyserial
pip install crcmod

# python3
apt install python3-psutil
pip3 install crcmod
pip3 install pyserial
pip3 install pyzmq
pip3 install pyinotify
pip3 install pika
pip3 install pynmea2
