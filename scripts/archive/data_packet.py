#!/usr/bin/env python
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import sys
from waggle.protocol.utils import packetmaker
from send import send


def data_packet(data):
    """
    This script makes a sensor packet and sends it to the NC.
    :param string data: The sensor data.
    """
    packet = packetmaker.make_data_packet(data)
    for pack in packet:
            send(pack)
