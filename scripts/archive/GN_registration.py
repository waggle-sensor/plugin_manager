#!/usr/bin/env python3
'''
A python script that creates a registration message packet and sends it to the NC.
'''
from waggle.protocol.utils import packetmaker
from send import send

NC_ID = open('/etc/waggle/NCID').read().strip()

packet = packetmaker.make_GN_reg(int(NC_ID))

print('Registration packet made. Sending to ', NC_ID)

for pack in packet:
    send(pack)
