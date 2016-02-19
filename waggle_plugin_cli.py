#!/usr/bin/env python

import sys, os, json, socket, time, select


from tabulate import tabulate

socket_file = '/tmp/plugin_manager'

def print_table(obj):
    print "%s:" % (obj['title'])
    print tabulate(obj['data'], obj['header'], tablefmt="psql")
    print "\n"


def print_tables(results):
    for obj in results['objects']:
        print_table(obj)
    
    
    
def command_dummy(results):
    print json.dumps(results, sort_keys=True, indent=4, separators=(',', ': '))
    

def read_streaming_api():
    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    try:
        client_sock.connect(socket_file)
    except Exception as e:
        print "Error connecting to socket: %s" % (str(e))
        client_sock.close()
        return None
        
        
    while 1:    
        try:
            data = client_sock.recv(2048) #TODO need better solution
        except Exception as e:
            print "Error reading socket: %s" % (str(e))
            client_sock.close()
            break
        print data


    
def read_api(command, timeout=3): 
    
    
    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    #client_sock.setblocking(0)
    
    client_sock.settimeout(timeout)
    try:
        client_sock.connect(socket_file)
    except Exception as e:
        print "Error connecting to socket: %s" % (str(e))
        client_sock.close()
        return None
        
    try:
        client_sock.sendall(command)
    except Exception as e:
         print "Error talking to socket: %s" % (str(e))
         client_sock.close()
         return None   

    #ready = select.select([mysocket], [], [], timeout_in_seconds)
    try:
        data = client_sock.recv(2048) #TODO need better solution
    except Exception as e:
        print "Error reading socket: %s" % (str(e))
        client_sock.close()
        return None
        

    client_sock.close()


    
    try:
        results = json.loads(data.rstrip())
    except Exception as e:
        return {'status' : 'error', 'message':'Could not parse JSON: '+str(e)}
    
    return results


def execute_command(command_line):
    if not command_line:
        command_line = ['list']
    
    command = command_line[0]
    try:
        command_function = command_functions[command]
    except KeyError:
        print "Command \"%s\" unknown." % (command)
        return

    results = read_api(" ".join(command_line), timeout = 20)
    
    if not results:
        print "read_api() returned no results"
        return
    
    if 'status' in results:
        if results['status']=='error':
            if 'message' in results:
                print 'error: ', results['message']
            else:
                print 'error, but got no specifc error message.'
            return

    try:
        command_function(results)
    except Exception as e:
        print 'DATA: "%s"' % (str(data))
        print "error: "+str(e)
    



if __name__ == '__main__':


    command_functions={
        'help': print_tables,
        'list': print_tables,
        'start' : command_dummy,
        'stop' : command_dummy
    }
    
    
    execute_command(['help'])
    
    
    while True:
        #execute_command(['list'])
        
        command_line = None
        try:
            command_line = raw_input('\nEnter your command: ')
        except KeyboardInterrupt:
            print "leaving..."
            sys.exit(0)
            
        #print command_line
        #print command_line.split()
        
        command_array = command_line.split()
        
        if command_array[0] == 'log':
            read_streaming_api()
            continue
        
        execute_command(command_array)
        


   
  
    