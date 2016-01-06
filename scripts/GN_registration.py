#!/usr/bin/env python


import sys
sys.path.append('../waggle_protocol/')
from utilities import packetmaker
from send import send


""" 
    A python script that creates a registration message packet and sends it to the NC. 
""" 

#Get the NC's unique ID
with open('/etc/waggle/NCID','r') as file_:
    NC_ID = file_.read().strip() 

#send registration to NC
#destination ID
packet = packetmaker.make_GN_reg(int(NC_ID))
print 'Registration packet made. Sending to ', NC_ID 
for pack in packet:
    send(pack)

