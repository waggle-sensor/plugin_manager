import time, socket, sys, logging


logger = logging.getLogger(__name__)



#gets the IP address for the nodecontroller
with open('/etc/waggle/node_controller_host','r') as file_:
    NC_HOST = file_.read().strip() 

NC_PORT = 9090 #port for push_server
    
def send(msg):
    
    """ 
    
        This is a client socket that connects to the push_server of the node controller to send messages. 
        
        :param string msg: The packed waggle message that needs to be sent.
        
    """

    #TODO May want to add guestnode message robustness. Currently, if node controller is currently unavailable, all guest node messages are lost. Can add a loop or
    #TODO Can add robustness by making this a daemon process that plugins can connect to using unix sockets. Send process puts messages in a queue to add robustness. 
    #TODO Send process can pull messages and send to NC if connected or hold on to the messages until NC connects. 
   
    
    s = None
    try: 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except Exception as e: 
        logger.error("Could not create socket to %s:%d : %s" % (NC_HOST, NC_PORT, str(e)))
        raise    
        
    try: 
        s.connect((NC_HOST,NC_PORT))
    except Exception as e: 
        logger.error("Could not connect to %s:%d : %s" % (NC_HOST, NC_PORT, str(e)))
        raise
        
    try:
        s.send(msg)
    except Exception as e: 
        logger.error("Could not send message to %s:%d : %s" % (NC_HOST, NC_PORT, str(e)))
        raise
   
    logger.debug("Did send message to nodecontroller.")
    
    if s:
        s.close()
