import time, serial, sys, datetime, pprint, logging, socket, os
#sys.path.append('../waggle_protocol/')
#from utilities import packetmaker
from multiprocessing import Queue

from queue import Full


logger = logging.getLogger(__name__)

class register(object):
    def __init__(self, name, man, plugin_mailbox, listeners):
    	man[name] = 1
        
        sr = system_router(name, man, plugin_mailbox, listeners)
        
        try:
            sr.route()
        except KeyboardInterrupt:
            sys.exit(0)
        


def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True
        
        

class system_router(object):
    
    def __init__(self,name, man, plugin_mailbox, listeners):
        self.name = name
        self.man = man
        self.plugin_mailbox = plugin_mailbox
        self.listeners = listeners
        
        
    
    def route(self):
        
        check_interval = 10
        
        for listener_uuid in self.listeners:
            logger.info("listener: %s" % (self.listeners[listener_uuid]['name']))
            
        last_check = time.time()
        delete_listeners = []
        while self.man[self.name]:
            
            # TODO select.select statment to read from multiple plugin queues
            msg = self.plugin_mailbox.get() # a blocking call.
            
            
            check_listener = 0
            current = time.time()
            
            if current > (last_check + check_interval):
                check_listener = 1
                last_check = current
            
            
            for listener_uuid in self.listeners:
                
                #logger.debug("listener: %s" % (listener_name))
                listener = self.listeners[listener_uuid]
                queue = listener['queue']
                
                do_send = 1
                
                if check_listener and ('pid' in listener):
                    pid = listener['pid']
                    
                    if not check_pid(pid):
                        logger.info("Listener process %s is not running anymore, pid: %d" % (listener['name'], pid))
                        do_send = 0
                        delete_listeners.append(listener_uuid)
                        
                    else:
                        logger.debug("Listener process %s is still running, pid: %d" % (listener['name'], pid))
                        
                if do_send:
                    try:
                        queue.put(msg)
                    except Queue.Full:
                        logger.warning("Queue %s is full, cannot push messages" % (listener_name))
                    except Exception as e:
                        logger.error("Error trying to put message into queue %s (%s): %s" % (listener['name'], str(type(e)), str(e)))
            
            # clean up
            if delete_listeners:
                for listener_uuid in delete_listeners:
                    del self.listeners[listener_uuid]
                delete_listeners = []
                    
                    
                    
