#!/usr/bin/env python3
import time, random

class register(object):
    
  def __init__(self, name, man, mailbox_outgoing):
    import time
    man[name] = 1
    interval = 8

    while man[name] == 1:
      timestamp_utc = int(time.time())
      timestamp_date  = time.strftime('%Y-%m-%d', time.gmtime(timestamp_utc))
      
      number = random.uniform(0., 99.)
      sendData=[str(timestamp_date).encode('iso-8859-1'), 'fake_sensor'.encode('iso-8859-1'), str(number).encode('iso-8859-1')]
      
      print('Sending data: ',sendData)
      
      mailbox_outgoing.put(sendData)
      #send a packet every 10 seconds
      time.sleep(interval)
        




