#!/usr/bin/env python
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
'''
A python script that creates a de-registration message packet for a GN and
sends it to the NC. A de-registration message needs to be sent before
disconnecting a guest node from a node controller.
'''
from waggle.protocol.utils import packetmaker
from send import send


NC_ID = open('/etc/waggle/NCID').read().strip()

# send de-registration to NC
packet = packetmaker.deregistration_packet(int(NC_ID))
print('De-registration packet made. Sending to ', NC_ID)

for pack in packet:
    send(pack)
