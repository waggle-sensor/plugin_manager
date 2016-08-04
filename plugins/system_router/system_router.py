#!/usr/bin/env python3

import time, serial, sys, datetime, pprint, logging, socket, os
#sys.path.append('../waggle_protocol/')
#from utilities import packetmaker
from multiprocessing import Queue

from queue import Full


logger = logging.getLogger(__name__)

class register(object):
    def __init__(self, name, man, mailbox_outgoing, mailbox_incoming, listeners):
        man[name] = 1

        sr = system_router(name, man, mailbox_outgoing, mailbox_incoming, listeners)

        try:
            sr.run()
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
    
    def __init__(self,name, man, mailbox_outgoing, mailbox_incoming, listeners):
        self.name = name
        self.man = man
        self.outgoing = mailbox_outgoing
        self.incoming = mailbox_incoming
        self.routingTable = listeners
        self.blockingTimeout = 3

    def routing(self, msg, incoming=False):
        mj = msg['msg_mj_type']
        mi = msg['msg_mi_type']
        if not mj or not mi:
            msg['error'] = "msg_mj_type or mi_type not presented"
            return msg

        # outgoing messages
        if not incoming:
            self.outgoing.put(msg)
            return msg

        # incoming messages
        puid = msg['r_puid']
        if not puid or len(puid) != 8:    # length must be 8 bytes hex string
            msg['error'] = "wrong puid"
            return msg

        # if no routing info, ignore the msg
        if not puid in self.routingTable:
            msg['error'] = "no puid matched in the routing table"
            return msg

        plugin = self.routingTable[puid]
        queue = plugin['incoming_queue']
        queue.put(msg)
        return msg

    def run(self):
        
        check_interval = 10
        
        for listener_uuid in self.routingTable:
            logger.info("listener: %s" % (self.routingTable[listener_uuid]['name']))
            
        last_check = time.time()
        delete_listeners = []
        while self.man[self.name]:
            
            # TODO select.select statment to read from multiple plugin queues
            msg = self.plugin_mailbox.get() # a blocking call.
            
            # check message from system_receive
            if not self.incoming.empty():
                msg = self.incoming.get(timeout=self.blockingTimeout)
                routing(msg, incoming=True)

            # check queues of user plugins
            for puid in self.routingTable:
                plugin = self.routingTable[puid]
                queue = plugin['outgoing_queue']
                if not queue.empty():
                    msg = queue.get(timeout=self.blockingTimeout)
                    msg['s_puid'] = puid
                    ret = routing(msg)
                    # if msg cannot be routed, return to the plugin
                    if not ret['error']:
                        return_queue = plugin['incoming_queue']
                        return_queue.put(ret)

            # prevents having very fast loop
            time.sleep(1)