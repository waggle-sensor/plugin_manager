#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
'''
A python script that creates, packs, and sends a ping.
'''
import sys
from waggle.protocol.utils import packetmaker
from send import send

packet = packetmaker.make_ping_packet()
print('Ping packet made...')
for pack in packet:
    send(pack)
