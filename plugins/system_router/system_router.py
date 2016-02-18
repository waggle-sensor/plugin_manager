import time, serial, sys, datetime, pprint, logging, socket, os
#sys.path.append('../waggle_protocol/')
#from utilities import packetmaker
from multiprocessing import Queue



logger = logging.getLogger(__name__)

class register(object):
    def __init__(self, name, man, plugin_mailbox, listeners):
    	man[name] = 1
        
        ss = system_router(plugin_mailbox, listeners)
        
        try:
            ss.read_mailbox(name, man)
        except KeyboardInterrupt:
            sys.exit(0)
        

class system_router(object):
    
    def __init__(self,plugin_mailbox, listeners):
        self.plugin_mailbox = plugin_mailbox
        self.listeners = listeners
        
        self.route()
        
    
    def route(self):
        
        while man[name]:
            
            # TODO select.select statment to read from multiple plugin queues
            msg = self.plugin_mailbox.get() # a blocking call.
            
            for listener_name in self.listeners:
                logger.debug("listener: %s" % (listener_name))
                queue = self.listeners[listener_name]
                
                try:
                    queue.put(msg)
                except Queue.Full:
                    logger.warning("Queue %s is full, cannot push messages" % (listener_name))
                except Exception as e:
                    logger.error("Error trying to put message into queue %s: %s" % (listener_name, str(e)))
