#!/usr/bin/env python
import multiprocessing, time, sys, re, os, logging, socket, json
import plugins 
import run_plugins_multi
from tabulate import tabulate

sys.path.append('../waggle_protocol/')
from utilities import packetmaker



LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - line=%(lineno)d - %(message)s'
formatter = logging.Formatter(LOG_FORMAT)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)


logger = logging.getLogger(__name__)
logger.handlers = []
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

#root_logger = logging.getLogger()
#root_logger.handlers = []
#root_logger.addHandler(handler)



class PluginManagerAPI:
    def __init__(self):
        self.plug = run_plugins_multi.plugin_runner()
        self.system_plugins={}
        self.system_plugins['system_send']=1
        self.command_functions = {
            "list" : self.list_plugins_full,
            "help" : self.help,
            "start" : self.start_plugin,
            "stop" : self.stop_plugin
        }
        self.blacklist = self.get_list('plugins/blacklist.txt')
        self.whitelist = self.get_list('plugins/whitelist.txt')

    #instructions for user
    def help_dialogue(self):
        print '\nIf you want to work with a specific plugin, enter the name of the plugin you would like to manipulate. \nEnter "startall" if you would like to activate all non-blacklisted plugins.\nUse "whitelist" or "blacklist" to view them. \nUse "stopall" to stop all plugins, or "killall" to kill all plugins. \nUse "pauseall" or "unpauseall" to pause and unpause active plugins. \nUse "startwhite" or "sw" to start plugins from the whitelist. \nType "list" or "l" for a list of available plugins. \nType "quit" or "q" to exit. \n\n'

    #takes a plugin name and adds or removes it from the blacklist or whitelist, as specified by caller
    def manip_list(self, plugin, listtype, manipulation):
        if (listtype == "whitelist"):
            file = open('plugins/whitelist.txt','r+')
            if (self.on_blacklist(plugin)):
                print 'Error: Plugin',plugin,'on blacklist. Cannot be on both lists.'
        elif (listtype == "blacklist"):
            file = open('plugins/blacklist.txt','r+')
            if (on_whitelist(plugin)):
                print 'Error: Plugin',plugin,'on whitelist. Cannot be on both lists.'
        li = file.read()
        li = re.split('\n', li)
        if (manipulation == "rm"):
            if (plugin in li):
                li.remove(plugin)
                li = "\n".join(li)
                file.seek(0)
                file.truncate()
                file.write(li)
                return 1
            else:
                return 0
        if (manipulation == "add"):
            if (not (plugin in li)):
                li.insert(0,plugin)
                li = "\n".join(li)
                file.seek(0)
                file.write(li)
                return 1
            else:
                return 0

    #Starts all whitelisted plugins
    def start_whitelist(self):
    
        whitelist = self.get_whitelist()
        fail = 0
        for name in whitelist:
            start = self.plug.start_plugin(name)
            if (not start) and (not name == ""):
                print 'Failed to start plugin', name
                fail = fail + 1
        if (fail == 0):
            print "Started all %d whitelisted plugins." % (len(whitelist))
        else:
            print "Attempted to start all whitelisted plugins, failed to start %d plugins" % (fail)

    #Starts all non-blacklisted plugins
    def start_all_valid(self):
    
        blacklist = self.get_blacklist()
        fail = 0
        for plugin in plugins.__all__:
            if (not (plugin in blacklist)):
                start = self.plug.start_plugin(plugin)
                if not start:
                    print 'Failed to start plugin', plugin
                    fail = fail + 1
        if (fail == 0):
            print "Started all non-blacklisted plugins."
        else:
            print "Attempted to start all non-blacklisted plugins, failed to start", fail

    def read_file(self, str ):
        if not os.path.isfile(str) :
            return ""
        with open(str,'r') as file_:
            return file_.read().strip()
        return ""


    def get_list(self, file):
        mylist = self.read_file(file)
        mylist = re.split('\n', mylist)
        mylist = filter(None, mylist)
        return mylist

    def get_blacklist(self):
        return self.blacklist

    def get_whitelist(self):
        return self.whitelist
    

    #Checks if the plugin is on the blacklist
    def on_blacklist(self, name):
        return (name in self.get_blacklist())

    #Checks if the plugin is on the whitelist
    def on_whitelist(self, name):
        return (name in self.get_whitelist())

    #Lists available plugins, if they are active, and whether they are present on the whitelist and blacklist
    def list_plugins_full(self):
        headers                                                       = ["plugin", "instance", "active", "whitelist", "blacklist"]
        system_table                                                  = []
        user_table                                                    = []
    
        #tabulate(table, headers, tablefmt                            = "fancy_grid")
    
    
        for name in plugins.__all__:
            if name in self.system_plugins:
                table                                                 = system_table
            else:
                table                                                 = user_table
            plugin                                                    = getattr(plugins, name)
            active                                                    = 0
            for j in self.plug.jobs:
                if (j.name == name):
                    #print 'Plugin', name, 'is active. Whitelist:', on_whitelist(name), '  |  Blacklist:', on_blacklist(name)
                    table.append([name, "", True, self.on_whitelist(name), self.on_blacklist(name)])
                    active                                            = 1
                    break
            if (not active):
                #print 'Plugin', name, 'is inactive. Whitelist:', on_whitelist(name), '  |  Blacklist:', on_blacklist(name)
                table.append([name, "", False, self.on_whitelist(name), self.on_blacklist(name)])
    
            
        #client_sock.sendall('System plugins:'+"\n")
        #client_sock.sendall(tabulate(system_table, headers, tablefmt = "fancy_grid"))
        #client_sock.sendall(str(system_table)+"\n")
        #client_sock.sendall('User plugins:'+"\n")
        #client_sock.sendall(str(user_table)+"\n")
    
        results                                                       = {}
        results['objects']                                            = []
    
        system_obj                                                    = {}
        system_obj['type']                                            = 'table'
        system_obj['title']                                           = 'System plugins'
        system_obj['header']                                          = headers
        system_obj['data']                                            = system_table
    
    
        user_obj                                                      = {}
        user_obj['type']                                              = 'table'
        user_obj['title']                                             = 'User plugins'
        user_obj['header']                                            = headers
        user_obj['data']                                              = user_table
    
        results['objects'].append(system_obj)
        results['objects'].append(user_obj)
    
        results['status']                                             = 'success'
        return json.dumps(results)
    
    
        #client_sock.sendall(tabulate(user_table, headers, tablefmt   = "fancy_grid"))


    def start_plugin(self, plugin):
        result                                                        = {}
        if (self.on_blacklist(plugin)):
            message                                                   = 'Cannot start plugin', plugin, 'because it is blacklisted.'
        
            result['status']                                          = 'error'
            result['message']                                         = message
        
            return json.dumps(result)
            
         
        started = self.plug.start_plugin(plugin)
        
        if started:
            result['status']    = 'success'
            return json.dumps(result)
        else:
            result['status']    = 'error'
            return json.dumps(result)
        


    def stop_plugin(self, plugin):
        stopped = self.plug.stop_plugin(plugin)
        if stopped:
            result['status']    = 'success'
            return json.dumps(result)
        else:
            result['status']    = 'error'
            return json.dumps(result)
    

    


    def do_command(self, command_line):
    
        command = command_line[0]
    
        try:
            command_function                                          = self.command_functions[command]
        except KeyError:
            print "Command %s unknown." % (command)
            return '{"error":"command %s is unknown"}' % (command)
            sys.exit(1)
    
        arguments = command_line[1:]
        if len(arguments) > 0:
            return command_function(arguments)
        else:
            return command_function()
    
    
    
    
    
    
        if (command == "startall"):
            start_all_valid()
        elif (command == "killall" or command == "ka"):
            self.plug.kill_all()
        elif (command == "startwhite" or command == "sw"):
            self.start_whitelist()
        elif (command == "stopall"):
            self.plug.stop_all()
        elif (command == "pauseall"):
            self.plug.pause_all()
        elif (command == "unpauseall"):
            self.plug.unpause_all()
        elif (command == "whitelist"):
            whitelist                                                 = self.read_file('plugins/whitelist.txt')
            print "Whitelist:\n",whitelist
        elif (command == "blacklist"):
            blacklist                                                 = self.read_file('plugins/blacklist.txt')
            print "Blacklist:\n",blacklist
        elif (command == "infoall"):
            self.plug.info_all()

        #if the entry matches the name of a plugin, go to plugin menu
        elif (command in plugins.__all__):
            while True:
                print '\nWould you like to "start", "stop", "pause", "unpause", or "kill" the plugin? \nYou can also "blacklist" or "whitelist" the plugin, or get "info" on it. \nType "back" to go back to the main menu.'
                command2                                              = raw_input('Enter your command: ')
                if (command2 == "start"):
                    if (on_blacklist(command)):
                        print 'Cannot start plugin', command, 'because it is blacklisted.'
                    else: 
                        self.plug.start_plugin(command)
                    break
                elif (command2 == "kill" or command2 == "k"):
                    self.plug.kill_plugin(command)
                    break
                elif (command2 == "stop"):
                    self.plug.stop_plugin(command)
                    break
                elif (command2 == "pause" or command2 =="p"):
                    self.plug.pause_plugin(command)
                    break
                elif (command2 == "unpause"):
                    self.plug.unpause_plugin(command)
                    break
                elif (command2 == "pid"):
                    print 'Plugin',command+"'s PID:",self.plug.plugin_pid(command)
                    break
                elif (command2 == "info"):
                    self.plug.plugin_info(command)
                    break
                #elif (command2 == "suspend"):
                #    self.plug.suspend_plugin(command)
                #    break
                #elif (command2 == "resume"):
                #    self.plug.resume_plugin(command)
                #    break

                #Go to whitelist/blacklist process, choose whether to add or remove from list
                elif (command2 == "whitelist" or command2 == "blacklist"):
                    print 'Would you like to add or remove from', command2 + '?'
                    command3                                          = raw_input('Enter your command (add/remove): ')
                    if (command3 == "add"):
                        change                                        = self.manip_list(command,command2,"add")
                        if (change == 1):
                            print command, command2+"ed."
                        elif (change == 0):
                            print command, "already on", command2 + "."
                        break
                    if (command3 == "remove" or command3 == "rm"):
                        change                                        = self.manip_list(command,command2,"rm")
                        if change:
                            print command, "removed from", command2 + "."
                        else:
                            print command, "not on", command2 + "."
                        break
                    else:
                        print "I didn't understand your answer."

                elif (command2 == "back"):
                    break
                else:
                    print "I didn't understand your command \"%s\"." % (command2)

        #stops plugins (and kills if there's a stop failure) and exits the program            
        elif (command == "quit" or command == "q"):
            if (not (self.plug.stop_all() == 0)):
                self.plug.kill_all()
            return
    
        else:
            print "I didn't understand your command \"%s\". Type \"help\" or \"h\" to review commands." % (command)



    def help(self):
        help_text                                                     = '''
    Available commands:
      <plugin>       The name of the plugin you would like to manipulate.
      startall       Activate all non-blacklisted plugins.
      stopall        Stop all plugins
      killall        Kill all plugins.
      pauseall       Pause all active plugins
      unpauseall     
      infoall        Information on all running plugins.
      whitelist      Show whitelist.
      blacklist      Show blacklist
      startwhite     Start plugins from the whitelist.
      quit           Quit.


    The following plugins are available.
    '''

        return json.dumps({'help': help_text, 'status': 'success'})



if __name__ == '__main__':
    
    # TODO this guest node registration is not need when the plugin_manager
    # 
    try:
        pmAPI = PluginManagerAPI()
    
    
    
        print '\nAutomatically starting whitelisted plugins...'
        pmAPI.start_whitelist()
        time.sleep(2)
    

        #list_plugins_full(None)


        socket_file = '/tmp/plugin_manager'

        if os.path.exists(socket_file): #checking for the file
            os.remove(socket_file)


        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


        server_sock.bind(socket_file)

        # listen for clients
        server_sock.listen(5)
    
        
        while True:
        
            logger.debug("waiting for data")
        
            try:
                client_sock, address = server_sock.accept()
            except KeyboardInterrupt:
                logger.info("Shutdown requested...exiting")
                self.stop()
                sys.exit(0)
            except Exception as e:
                logger.info("server_sock.accept: "+str(e))
                self.stop()
                sys.exit(1)


            try:
                data = client_sock.recv(8192) #arbitrary
        
            except KeyboardInterrupt, k:
                logger.info("KeyboardInterrupt")
                break
            except Exceptiomn as a:
                logger.error("client_sock.recv failed: %s" % (str(e) ))
                break    
        
        
            command = str(data).rstrip()
            logger.debug("received command \"%s\"" % (command))
            result_json = pmAPI.do_command(command.split())
        
            try:
                client_sock.sendall(result_json+"\n")
            except Exception as e:
                logger.warning("Could not reply: %s" % (str(e)) )
                continue
        
            logger.debug("got data: \"%s\"" % (str(data)))
        
        
    except KeyboardInterrupt:
        print "exiting..."
    except Exception as e:
        print "error: "+str(e)
    
   