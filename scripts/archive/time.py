#!/usr/bin/env python3
'''
A python script that creates and sends a time request.
'''
from waggle.protocol.utils import packetmaker
from send import send

packet = packetmaker.make_time_packet()
print('Time request packet made...')
for pack in packet:
        send(pack)
