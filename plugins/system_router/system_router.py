import time, serial, sys, datetime, pprint, logging, socket, os
#sys.path.append('../waggle_protocol/')
#from utilities import packetmaker
from multiprocessing import Queue



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
        
        for listener_name in self.listeners:
            logger.info("listener: %s" % (listener_name))
            
        last_check = time.time()
        while self.man[self.name]:
            
            # TODO select.select statment to read from multiple plugin queues
            msg = self.plugin_mailbox.get() # a blocking call.
            
            
            check_listener = 0
            current = time.time()
            
            if current > (last_check + check_interval):
                check_listener = 1
                last_check = current
            
            for listener_name in self.listeners:
                
                #logger.debug("listener: %s" % (listener_name))
                listener = self.listeners[listener_name]
                queue = listener['queue']
                
                do_send = 1
                
                if check_listener and ('pid' in listener):
                    pid = listener['pid']
                    
                    if not check_pid(pid):
                        logger.info("Listener process is not running anymore, pid: %d" % (pid))
                        do_send = 0
                        del self.listeners[listener_name]
                    else:
                        logger.debug("Listener process is still running, pid: %d" % (pid))
                        
                if do_send:
                    try:
                        queue.put(msg)
                    #except Queue.Full:
                    #    logger.warning("Queue %s is full, cannot push messages" % (listener_name))
                    except Exception as e:
                        logger.error("Error trying to put message into queue %s (%s): %s" % (listener_name, str(type(e)), str(e)))
                    
                    
