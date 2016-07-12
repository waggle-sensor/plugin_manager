#!/usr/bin/env python3

import time, socket, sys, logging
from multiprocessing import Process, Queue
from lib.msg_handler import msg_handler



logger = logging.getLogger(__name__)

class register(object):

    def __init__(self, name, man, mailbox_outgoing):
        
        man[name] = 1
        
        sr = system_receive(name, man)
        
        try:
            sr.receive()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            logger.error("Exception (%s): %s" % (str(type(e)), str(e)))
            sys.exit(1)    
        
        
class system_receive:
    """
    This class receives messages from the node controller for the plugin manager and/or plugins. 
    """
    def __init__(self, name, man):
        
        self.name = name
        self.man = man
        
        with open('/etc/waggle/node_controller_host','r') as file_:
            self.NC_HOST = file_.read().strip()
        logger.info("NC_HOST: %s" % (self.NC_HOST))

        self.NC_PORT = 9091 #port for pull_server
        logger.info("NC_PORT: %s" % (self.NC_PORT))

        with open('/etc/waggle/node_id','r') as file_:
            self.NODE_ID = file_.read().strip()
    
    
    
    def receive(self):
        connection_error = False
        while self.man[self.name]: #loop that keeps connecting to node controller
        
            if connection_error:
                if s:
                    s.close()
                    
                time.sleep(3)
                connection_error = False
                
        
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.NC_HOST,self.NC_PORT))
            except Exception as e: 
                logger.error('Unable to connect to %s:%d : %s' % (self.NC_HOST, self.NC_PORT, str(e)))
                connection_error = True
                continue
        
        
            # Contact node controller to 
            try:
                s.send(self.NODE_ID)
            except Exception as e: 
                 #waits for pull request to go through #TODO might be unneccessary 
                logger.error('Unable to send initial request: %s' % (str(e)))
                connection_error = True
                continue
                
            time.sleep(1)
            # 
            try:
                msg = s.recv(4028) #arbitrary. Can put in a config file
            except Exception as e: 
                logger.error('Error receiving message from node controller: %s' % (str(e)))
                connection_error = True
                continue
        
            if not msg:
                s.close()
                time.sleep(1)
                
                
            logger.debug("incoming message: %s" % (msg))
            try:
                #sends incoming messages to msg_handler class 
                msg_handler(msg)
                s.close() #closes each time a message is received. 
                #print 'Connection closed...'
            except Exception as e:
                logger.error('Unpack unsuccessful: %s' % (str(e)))
       
                    
            if s:
                s.close()
                
                
                