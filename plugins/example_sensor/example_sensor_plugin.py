#!/usr/bin/env python3
import time, serial, sys, os, random

class register(object):
    
    def __init__(self, name, man, mailbox_outgoing):
        import time
        man[name] = 1

        temperature_file = '/sys/class/thermal/thermal_zone0/temp'
        interval = 8

        use_temp = 0
        if os.path.isfile(temperature_file):
            use_temp = 1 
            
            
        count = 0
        while man[name] == 1:
            
            timestamp_utc = int(time.time())
            timestamp_date  = time.strftime('%Y-%m-%d', time.gmtime(timestamp_utc))
            timestamp_epoch = timestamp_utc * 1000
            
            if use_temp:
                tempC = int(open(temperature_file).read()) / 1e3
                sendData=[str(timestamp_date).encode('iso-8859-1'),'example_sensor'.encode('iso-8859-1'), '1'.encode('iso-8859-1'), 'default'.encode('iso-8859-1'), '%d' % (timestamp_epoch), 'CPU temperature'.encode('iso-8859-1'), "meta.txt".encode('iso-8859-1'), [str(tempC).encode('iso-8859-1')]]
            else:
                rint = random.randint(1, 100)
                sendData=[str(timestamp_date).encode('iso-8859-1'), 'example_sensor'.encode('iso-8859-1'), '1'.encode('iso-8859-1'), 'default'.encode('iso-8859-1'), '%d' % (timestamp_epoch), 'RandomNumber'.encode('iso-8859-1'), "meta.txt".encode('iso-8859-1'), [str(rint).encode('iso-8859-1')]]
            
            print('Sending data: ',sendData)
            
            mailbox_outgoing.put(sendData)
            #send a packet every 10 seconds
            time.sleep(interval)
            count = count + 1
        




