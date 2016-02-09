#!/usr/bin/env python

import sys, os, json


from tabulate import tabulate






#tabulate(system_table, headers, tablefmt="fancy_grid")


if __name__ == '__main__':

    socket_file = '/tmp/plugin_manager'


    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


    server_sock.connect(socket_file)


    client_sock.sendall('list')
    
    data = client_sock.recv(2048)
    
    
    
    client_sock.close()


    print str(data)