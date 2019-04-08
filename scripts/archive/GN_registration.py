#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
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
