#!/usr/bin/env python


import sys
sys.path.append('../waggle_protocol/')
from utilities import packetmaker
from send import send


""" 
    A python script that creates, packs, and sends a ping. 
""" 

packet = packetmaker.make_ping_packet()
print 'Ping packet made...' 
for pack in packet:
    send(pack)
