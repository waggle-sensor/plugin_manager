#!/usr/bin/env python3
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
