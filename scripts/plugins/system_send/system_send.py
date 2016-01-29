import time, serial, sys, datetime, pprint, logging, socket
sys.path.append('../waggle_protocol/')
from utilities import packetmaker
from multiprocessing import Queue



class register(object):
    def __init__(self, name, man, mailbox_outgoing):
    	man[name] = 1
        read_mailbox(mailbox_outgoing)



def read_mailbox(mailbox_outgoing):

    logger = logging.getLogger(__name__)
    
    with open('/etc/waggle/NCIP','r') as file_:
        NCIP = file_.read().strip() 
    
    with open('/etc/waggle/hostname','r') as file_:
        HOSTNAME = file_.read().strip()


    HOST = NCIP #sets to NodeController IP
    PORT = 9090 #port for push_server
    
    
    s = None
    while 1:
         
        msg = mailbox_outgoing.get() # a blocking call.
         
        while 1:
            if not s:
                try: 
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                except Exception as e: 
                    logger.error("Could not create socket to %s:%d : %s" % (HOST, PORT, str(e)))
                    continue    
        
        
            try: 
                s.connect((HOST,PORT))
            except Exception as e: 
                logger.error("Could not connect to %s:%d : %s" % (HOST, PORT, str(e)))
                continue
        
            try:
                s.send(msg)
            except Exception as e: 
                logger.error("Could not send message to %s:%d : %s" % (HOST, PORT, str(e)))
                continue
   
   
            #TODO get ack
            
            logger.debug("Did send message to nodecontroller.")
    
            if s:
                s.close()
            
            # once message msg has been delivered, the inner loop can be left.    
            break
         
         