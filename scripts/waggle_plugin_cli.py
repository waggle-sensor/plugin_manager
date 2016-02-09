#!/usr/bin/env python

import sys, os, json, socket, time


from tabulate import tabulate



def command_list(results):

    for obj in results['objects']:
        print "%s:" % (obj['title'])
        print tabulate(obj['data'], obj['header'], tablefmt="fancy_grid")
        print "\n"
    
    
def command_help(results):
    print results['help']
    
    
def read_api(command): 
    socket_file = '/tmp/plugin_manager'
    
    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


    client_sock.connect(socket_file)


    client_sock.sendall(command)

    data = client_sock.recv(2048) #TODO need better solution


    client_sock.close()


    

    results = json.loads(data.rstrip())
    
    
    return results


def execute_command(command):
    try:
        command_function = command_functions[command]
    except KeyError:
        print "Command %s unknown." % (command)
        sys.exit(1)

    results = read_api(command)
    

    try:
        command_function(results)
    except Exception as e:
        print 'DATA: "%s"' % (str(data))
        print "error: "+str(e)
    



if __name__ == '__main__':


    command_functions={
        'help': command_help,
        'list': command_list
    }
    
    
    execute_command('help')
    execute_command('list')
    
    while True:
        
        command = raw_input('\nMain menu\nEnter your command: ')
    
        execute_command(command)
        


   
  
    