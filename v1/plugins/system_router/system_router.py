#!/usr/bin/env python3
import time
import sys
import logging
import os
from multiprocessing import Queue


logger = logging.getLogger(__name__)


class register(object):
    # def __init__(self, name, man, mailbox_outgoing, mailbox_incoming, listeners):
    #     man[name] = 1

    #     sr = system_router(name, man, mailbox_outgoing, mailbox_incoming, listeners)
    def __init__(self, name, man, plugin_mailbox, listeners):
        man[name] = 1

        sr = system_router(name, man, plugin_mailbox, listeners)
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

    # def __init__(self,name, man, mailbox_outgoing, mailbox_incoming, listeners):
    #     self.name = name
    #     self.man = man
    #     self.outgoing = mailbox_outgoing
    #     self.incoming = mailbox_incoming
    #     self.routingTable = listeners
    #     self.blockingTimeout = 3

    # def routing(self, msg, incoming=False):
    #     mj = msg['msg_mj_type']
    #     mi = msg['msg_mi_type']
    #     if not mj or not mi:
    #         msg['error'] = "msg_mj_type or mi_type not presented"
    #         return msg

    #     # outgoing messages
    #     if not incoming:
    #         self.outgoing.put(msg)
    #         return msg

    #     # incoming messages
    #     puid = msg['r_puid']
    #     if not puid or len(puid) != 8:    # length must be 8 bytes hex string
    #         msg['error'] = "wrong puid"
    #         return msg

    #     # if no routing info, ignore the msg
    #     if not puid in self.routingTable:
    #         msg['error'] = "no puid matched in the routing table"
    #         return msg

    #     plugin = self.routingTable[puid]
    #     queue = plugin['incoming_queue']
    #     queue.put(msg)
    #     return msg
    def __init__(self,name, man, plugin_mailbox, listeners):
        self.name = name
        self.man = man
        self.plugin_mailbox = plugin_mailbox
        self.listeners = listeners

    def run(self):
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
        # check_interval = 10

        # for listener_uuid in self.routingTable:
        #     logger.info("listener: %s" % (self.routingTable[listener_uuid]['name']))

        # last_check = time.time()
        # delete_listeners = []
        # while self.man[self.name]:

        #     # TODO select.select statment to read from multiple plugin queues
        #     # msg = self.plugin_mailbox.get() # a blocking call.

        #     # check message from system_receive
        #     if not self.incoming.empty():
        #         msg = self.incoming.get(timeout=self.blockingTimeout)
        #         routing(msg, incoming=True)
        #     logger.debug(len(self.routingTable))
        #     # check queues of user plugins
        #     for puid in self.routingTable:
        #         plugin = self.routingTable[puid]
        #         queue = plugin['outgoing_queue']
        #         if not queue.empty():
        #             msg = queue.get(timeout=self.blockingTimeout)
        #             msg['s_puid'] = puid
        #             ret = routing(msg)
        #             # if msg cannot be routed, return to the plugin
        #             if not ret['error']:
        #                 return_queue = plugin['incoming_queue']
        #                 return_queue.put(ret)

        #     # prevents having very fast loop
        #     time.sleep(1)
