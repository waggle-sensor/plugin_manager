#!/usr/bin/env python
import time, serial, sys, datetime, os, random
sys.path.append('../../')
from waggle_protocol.utilities import packetmaker
#sys.path.append('../Communications/')
#from internal_communicator import send
sys.path.append('../')
from send import send


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return long(unix_time(dt) * 1000.0)
    

class register(object):
    
    temperature_file = '/sys/class/thermal/thermal_zone0/temp'
    interval = 10
    
    def __init__(self, name, man):
        import time
        man[name] = 1

        if os.path.isfile(temperature_file): 
            count = 0
            while 1:
                tempC = int(open(temperature_file).read()) / 1e3
                sendData=['CPU temperature', int(unix_time_millis(datetime.datetime.now())), ['Temperature']  , ['i'], [tempC], ['Celsius'], ['count='+str(count)]]
                print 'Sending data: ',sendData
                #packs and sends the data
                packet = packetmaker.make_data_packet(sendData)
                for pack in packet:
                    send(pack)
                #send a packet every 10 seconds
                time.sleep(interval)
                count = count + 1
        
        else:
            count = 0
            while 1:
                rint = random.randint(1, 100)
                sendData=['RandomNumber', int(unix_time_millis(datetime.datetime.now())), ['Random']  , ['i'], [rint], ['NA'], ['count='+str(count)]]
                print 'Sending data: ',sendData
                #packs and sends the data
                packet = packetmaker.make_data_packet(sendData)
                for pack in packet:
                    send(pack)
                #send a packet every 10 seconds
                time.sleep(interval)
                count = count + 1



