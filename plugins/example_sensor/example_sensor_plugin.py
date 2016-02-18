#!/usr/bin/env python
import time, serial, sys, datetime, os, random



def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return long(unix_time(dt) * 1000.0)
    

class register(object):
    
    
    
    def __init__(self, name, man, mailbox_outgoing):
        import time
        man[name] = 1

        temperature_file = '/sys/class/thermal/thermal_zone0/temp'
        interval = 10

        use_temp = 0
        if os.path.isfile(temperature_file):
            use_temp = 1 
            
            
        count = 0
        while 1:
            if use_temp:
                tempC = int(open(temperature_file).read()) / 1e3
                sendData=['CPU temperature', int(unix_time_millis(datetime.datetime.now())), ['Temperature']  , ['i'], [tempC], ['Celsius'], ['count='+str(count)]]
            else:
                rint = random.randint(1, 100)
                sendData=['RandomNumber', int(unix_time_millis(datetime.datetime.now())), ['Random']  , ['i'], [rint], ['NA'], ['count='+str(count)]]
            
            print 'Sending data: ',sendData
            
            mailbox_outgoing.put(sendData)
            #send a packet every 10 seconds
            time.sleep(interval)
            count = count + 1
        




