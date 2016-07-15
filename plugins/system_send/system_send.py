#!/usr/bin/env python3

import time, serial, sys, datetime, pprint, logging, socket, os
from multiprocessing import Queue

sys.path.append('./waggle_protocol/')
from utilities import packetmaker

logging.basicConfig()
logger = logging.getLogger(__name__)


def read_file( str ):
    if not os.path.isfile(str) :
        return ""
    with open(str,'r') as file_:
        return file_.read().strip()
    return ""


class register(object):
    def __init__(self, name, man, mailbox_outgoing):
        man[name] = 1

        ss = system_send(mailbox_outgoing)

        try:
            ss.read_mailbox(name, man)
        except KeyboardInterrupt:
            sys.exit(0)
        

class system_send(object):
    
    def __init__(self,mailbox_outgoing):
        self.mailbox_outgoing = mailbox_outgoing
        self.socket = None
        self.HOST = read_file('/etc/waggle/node_controller_host')
        self.PORT = 9090 #port for push_server
        try:
            context = zmq.Context()
            self.socket = context.socket(zmq.REQ)
        except zmq.error.ZMQError as e:
            logger.debug("zmq.error.ZMQError: (%s) %s" % (str(type(e)), str(e)))
            msg = None
        logger.debug("Using %s:%d" % (self.HOST , self.PORT))
        
        packet = packetmaker.make_GN_reg(1)
    
        while 1:
            logger.info('Registration packet made. Sending to 1.')
            try:
                for pack in packet:
                    self.send(pack)
            except Exception as e:
                logger.error("Could not send guest node registration: %s" % (str(e)))
                time.sleep(2)
                continue
            break
    
    def send(self, msg):
        if self.socket:
            self.socket.close()

        try:
            self.socket = context.socket(zmq.REQ)
            self.socket.connect ("tcp://%s:%s" % (self.HOST, self.PORT))
            self.socket.send(msg)
        except:
            logger.error("Could not send message to %s:%d: %s" % (self.HOST, self.PORT, str(e)))
            raise

        # try: 
        #     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # except Exception as e: 
        #     logger.error("Could not create socket to %s:%d : %s" % (self.HOST, self.PORT, str(e)))
        #     raise

        # try: 
        #     self.socket.connect((self.HOST,self.PORT))
        # except Exception as e: 
        #     logger.error("Could not connect to %s:%d : %s" % (self.HOST, self.PORT, str(e)))
        #     raise

        # try:
        #     self.socket.send(msg)
        # except Exception as e: 
        #     logger.error("Could not send message to %s:%d : %s" % (self.HOST, self.PORT, str(e)))
        #     raise
            

    def read_mailbox(self, name, man):

        
        while man[name]:
         
            
            msg = self.mailbox_outgoing.get() # a blocking call.
           
         
            packet = packetmaker.make_data_packet(msg)
            for pack in packet:
                while 1:
                    try:
                        self.send(pack)
                    except KeyboardInterrupt as e:
                        raise
                    except Exception as e:
                        logger.error("Could not send message to %s:%d : %s" % (self.HOST, self.PORT, str(e)))
                    
                        time.sleep(2)
                        continue
                    break
            logger.debug("Did send message to nodecontroller.")
                
                
