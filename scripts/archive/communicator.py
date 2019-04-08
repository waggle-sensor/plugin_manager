#!/usr/bin/env python
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
from multiprocessing import Process, Queue
import time, socket, sys, logging, argparse
from msg_handler import msg_handler

"""
    This module contains the communication processes for the node. It receives messages from the NC and passes them to msg_handler.py.
    This process runs in the background after guest node configuration.
    
"""
#TODO add GN_scanner here, check if GN has been registered, if not, start GN scanner and register
#make a process, when it connects, write to file, use indicator to indicate that receive process can start running. 
#gets the IP address for the nodecontroller


# TODO: rename this script to distinguish it more clearly from nodecontroller scripts


LOG_FILENAME="/var/log/waggle/communicator.log"

logger = logging.getLogger(__name__)


# from: http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO, prefix=''):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
        self.prefix = prefix
 
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, self.prefix+line.rstrip())

    def flush(self):
        pass
        
        
        

with open('/etc/waggle/NCIP','r') as file_:
    NCIP = file_.read().strip() 
    
with open('/etc/waggle/hostname','r') as file_:
    HOSTNAME = file_.read().strip()
    




class receive(Process):
    """ 
        This is a client socket that connects to the pull_server of the node controller to retrieve messages. 
        
    """
    
    def run(self):
        HOST = NCIP #Should connect to NodeController
        PORT = 9091 #port for pull_server
        #if NCIP not == '':
        
        while True: #loop that keeps connecting to node controller
            try:
                try: 
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((HOST,PORT))
                    #print 'Receive process connected...'
                    request = HOSTNAME #device unique ID
                    s.send(request)
                    time.sleep(1) #waits for pull request to go through #TODO might be unneccessary 
                    #print 'Request sent: ', request
                    msg = s.recv(4028) #arbitrary. Can put in a config file
                    if msg != 'False':
                        logger.debug("incoming message: %s" % (msg))
                        try:
                            #sends incoming messages to msg_handler class 
                            msg_handler(msg)
                            s.close() #closes each time a message is received. 
                            #print 'Connection closed...'
                        except Exception as e:
                            logger.error('Unpack unsuccessful: %s' % (str(e)))
                    else:
                        s.close() #closes each time a message is received.
                        time.sleep(1)
                        
                except Exception as e: 
                    logger.error('Unable to connect to %s: %s' % (NCIP, str(e)))
                    s.close()
                    time.sleep(5)
            except Exception as e:
                logger.error('Connection disrupted...Socket shutting down. error: %s' % (str(e)) )
                if s:
                    s.close()
                break
        if s:
            s.close()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logging', dest='enable_logging', help='write to log files instead of stdout', action='store_true')
    args = parser.parse_args()
    
    
    if args.enable_logging:
        # 5 times 10MB
        sys.stdout.write('logging to '+LOG_FILENAME+'\n')
        log_dir = os.path.dirname(LOG_FILENAME)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10485760, backupCount=5)
        
        #stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(logger, logging.INFO, 'STDOUT: ')
        sys.stdout = sl
 
        #stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(logger, logging.ERROR, 'STDERR: ')
        sys.stderr = sl
        
        handler.setFormatter(formatter)
        root_logger.handlers = []
        root_logger.addHandler(handler)
    
    try:
        
        #start receiving messages
        msg_receive = receive()
        msg_receive.start()
               
    except KeyboardInterrupt, k: 
        msg_receive.terminate()
        logger.info('stopping...')

