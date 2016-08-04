#!/usr/bin/env python3

import os, psutil, subprocess, datetime, time, logging, socket, json
from collections import namedtuple
import pyinotify
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes

#********** SH_TEST_STRAT
# Get info using zeromq from wagman_publihser.py
import sys, zmp
import operator

nc_hb = 0
gn_hb = 0
cs_hb = 0

nc_cn = 0
gn_cn = 0
cs_cn = 0

wagman_info = {}

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

socket.connect ('ipc:///tmp/zeromq_wagman-pub')
# socket.setsockopt_string(zmq.SUBSCRIBE, sys.argv[1])
socket.setsockopt(zmq.SUBSCRIBE, ''.encode('latin-1'))
#********** SH_TEST_END

"""
	This plugin is to monitor and report systematic information and activities vary from temperature, disk space, and system information to status of plugins.
	This plugin also detects USB devices to launch corresponding plugin.
"""

#TODO: when exceptions happen it could send an error code corresponding to the error, not sending the heavy error message, to reduce payload of the message. 

logger = logging.getLogger(__name__)

# wm = WatchManager()
# mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  # watched events
autoplugins = {}

class register(object):
	def __init__(self, name, man, mailbox_outgoing):
		man[name] = 1
		base = base_plugin(name, man, mailbox_outgoing)
		base.run()

epoch = datetime.datetime.utcfromtimestamp(0)

def epoch_time(dt):
	return (dt - epoch).total_seconds() * 1000.0

def get_host_name():
	"""
		Returns host name containing which device (from uSD and eMMC) is used to boot 
	"""
	ret = ""
	try:
		ret = subprocess.getoutput(["uname -n"])
	except Exception as e:
		ret = "error on getting host name: %s" % (str(e))
	return ret

def get_boot_info(history_count):
	"""
		Returns history of reboot and shutdown.
	"""
	ret = ""
	try:
		ret = subprocess.getoutput(["last -x reboot | head -n %d" % (history_count)])
	except Exception as e:
		ret = "error on getting boot messages: %s" % (str(e))
	return ret

def get_shutdown_info(history_count):
	"""
		Returns history of reboot and shutdown.
	"""
	ret = ""
	try:
		ret = subprocess.getoutput(["last -x shutdown | head -n %d" % (history_count)])
	except Exception as e:
		ret = "error on getting shutdown messages: %s" % (str(e))
	return ret

def disk_usage(path):
	"""Return disk usage statistics about the given path.

	Returned valus is a named tuple with attributes 'total', 'used' and
	'free', which are the amount of total, used and free space, in bytes.
	"""
	total = used = free = 0
	ret = ""
	try:
		st = os.statvfs(path)
		free = st.f_bavail * st.f_frsize
		total = st.f_blocks * st.f_frsize
		used = (st.f_blocks - st.f_bfree) * st.f_frsize
		ret = "(total=%d, used=%d, free=%d)" % (total, used, free)
	except Exception as e:
		pass
	return ret

def get_current_cpu_temp():
	temperature_file = '/sys/class/thermal/thermal_zone0/temp'
	tempC = 0
	if os.path.isfile(temperature_file):
		tempC = int(open(temperature_file).read()) / 1e3
	else:
		tempC = -1000
	return tempC

def get_white_list():
	whitelist_file = '/usr/lib/waggle/plugin_manager/plugins/whitelist.txt'
	list = []
	if os.path.isfile(whitelist_file):
		try:
			with open(whitelist_file, 'r') as f:
				for line in f:
					if line.strip():
						list.append(line)
		except Exception as e:
			list = "error: %s" % (str(e))
	else:
		list = "error: does not exist"

	return list

def get_service_list():
	ret = ""
	try:
		raw = subprocess.getoutput(["waggle-service list"])
		splits = raw.split('\n')
		for line in splits:
			if 'waggle' in line:
				entities = line.split('|')
				for entity in entities:
					if not entity.strip() == '':
						ret += entity.strip() + ","
				ret += "|"
	except Exception as e:
		ret = "error on getting waggle-service list: %s" % (str(e))
	return ret

# def initialize_plugin():
# 	if plugin in whitelist:
# 		continue
# 	elif plugin == '':
# 		continue
# 	else:
# 		# Check if plugin alive
# 		cmd = "info %s" % (plugin)
# 		ret = self.send_command(cmd)
# 		if 'status' in ret and ret['status'] == 'success':
# 			continue
# 		else:
# 			# Start the plugin
# 			logger.debug("Try to start %s" % (plugin))
# 			cmd = "start %s" % (plugin)
# 			ret = self.send_command(cmd)
# 			if 'status' in ret and ret['status'] == 'success':
# 				logger.debug("%s is up and running" % (plugin))
# 				delete_plugins.append(device)
# 			else:
# 				logger.debug("%s failed to start" % (plugin))

# class PTmp(ProcessEvent):
# 	def process_IN_IGNORED (self, event):
# 		pass

# 	def process_IN_CREATE(self, event):
# 		global autoplugins
# 		logger.debug("%s detected" % (event.name))
# 		# for device in autoplugins:
# 		# 	if device == event.name:

# 	def process_IN_DELETE(self, event):
# 		global autoplugins
# 		logger.debug("%s rejected" % (event.name))

class base_plugin(object):
	plugin_name = 'base plugin'
	plugin_version = "1"
	def __init__(self, name, man, mailbox_outgoing):
		self.name = name
		self.man = man
		self.outqueue = mailbox_outgoing

	def get_boot_info(self):
		ret = ""

	def send(self, category, msg):
		timestamp_epoch = epoch_time(datetime.datetime.utcnow())

		self.outqueue.put([
			str(datetime.datetime.utcnow().date()).encode('iso-8859-1'),
			self.plugin_name.encode('iso-8859-1'),
			self.plugin_version.encode('iso-8859-1'),
			'default'.encode('iso-8859-1'),
			'%d' % (timestamp_epoch),
			category.encode('iso-8859-1'),
			'meta.txt'.encode('iso-8859-1'),
			msg
			])

	def send_command(self, command, timeout=3):
		socket_file = '/tmp/plugin_manager'
		client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		#client_sock.setblocking(0)

		client_sock.settimeout(timeout)
		try:
			client_sock.connect(socket_file)
		except Exception as e:
			print(("Error connecting to socket: %s" % (str(e))))
			client_sock.close()
			return None

		try:
			client_sock.sendall(command.encode('iso-8859-15'))
		except Exception as e:
			print(("Error talking to socket: %s" % (str(e))))
			client_sock.close()
			return None   

		#ready = select.select([mysocket], [], [], timeout_in_seconds)
		try:
			data = client_sock.recv(2048).decode('iso-8859-15') #TODO need better solution
		except Exception as e:
			print(("Error reading socket: %s" % (str(e))))
			client_sock.close()
			return None

		client_sock.close()

		try:
			results = json.loads(data.rstrip())
		except Exception as e:
			return {'status' : 'error', 'message':'Could not parse JSON: '+str(e)}

		return results

	def get_autostart_dict(self, base_path):
		autostart_file = '/usr/lib/waggle/plugin_manager/plugins/autostartlist.txt'
		dict = {}

		if os.path.isfile(autostart_file):
			try:
				with open(autostart_file, 'r') as file:
					for line in file:
						entity = line.split(':')
						dict[base_path + entity[0]] = entity[1].strip()
			except Exception as e:
				logger.debug("Failed to retreive autostart plugin list")
				pass
		return dict

	def collect_system_info(self):
		data = {}
		data['disk'] = disk_usage("/")
		data['host name'] = get_host_name()
		data['reboots'] = get_boot_info(3)
		data['shutdowns'] = get_shutdown_info(4)
		data['temperature'] = get_current_cpu_temp()

		return ['{}:{}'.format(keys, data[keys]).encode('iso-8859-1') for keys in data]

	def collect_service_info(self):
		data = {}
		data['whitelist'] = get_white_list()
		data['services'] = get_service_list()

		return ['{}:{}'.format(keys, data[keys]).encode('iso-8859-1') for keys in data]

	def collect_plugin_info(self):
		data = {}

		return ['{}:{}'.format(keys, data[keys]).encode('iso-8859-1') for keys in data]


	#********** SH_TEST_START
	def collect_wagman_info(self):
		global nc_hb, gn_hb, cs_hb
		global nc_cn, gn_cn, cs_cn 
		global wagman_info
		message = socket.recv_string()
		prefix, _, content = message.partition(':')
		prefix, _, content = (content.strip()).partition(' ')

		#********************************************#******************************************#
		# prefix									 # content									#
		#********************************************#******************************************#
		# id (wagman id)							 #											#
		# date (wagman system date)					 #											#
		# cu (consumming current in each power tab)  #											#
		# th (temperature difference between checks) #											#
		# fails (# of fail to turn on)				 #											#
		# enabled (tab status)						 #											#
		# media (boot media)						 #	SD / EMMC								#
		# gn (guest node)							 #	hbeat / start / fault timeout / killing	#
		# nc (nodecontroller)						 #	hbeat 									#
		# cs (coresense)							 #	hbeat / start							#
		#********************************************#******************************************#

		if prefix == "nc":
			if content == "heartbeat":
				nc_hb = nc_hb + 1
			else:
				nc_info = 'nc_info' + str(nc_cn)
				wagman_info[nc_info] = content
				nc_cn = nc_cn + 1


		elif prefix == "gn":
			if content == "heartbeat":
				gn_hb = gn_hb + 1
			else:
				gn_info = 'gn_info' + str(gn_cn)
				wagman_info[gn_info] = content
				gn_cn = gn_cn + 1

		elif prefix == "cs":
			if content == "heartbeat":
				cs_hb = cs_hb + 1
			else:
				cs_info = 'cs_info' + str(cs_cn)
				wagman_info[cs_info] = content
				cs_cn = cs_cn + 1

		else:
			wagman_info[prefix] = content

			if prefix == "media":
				wagman_info['hbeat_nc'] = str(nc_hb) + "/6"
				wagman_info['hbeat_gn'] = str(gn_hb) + "/6"
				wagman_info['hbeat_cs'] = str(cs_hb) + "/6"

				nc_hb = 0
				gn_hb = 0
				cs_hb = 0

				nc_cn = 0
				gn_cn = 0
				cs_cn = 0                

				sorted_wagman_info = sorted(wagman_info.items(), key=operator.itemgetter(0))

				# return sorted_wagman_info # list
				return wagman_info # dictionary
		#********** SH_TEST_END



	def run(self):
		global autoplugins
		# Wait 40 seconds for other services preparing to run
		# TODO: need to know when all system/services are green so this report can send right information of the current system status.
		time.sleep(40)
		data = self.collect_system_info()
		self.send('system info', data)
		data = self.collect_service_info()
		self.send('service info', data)
		

		#********** SH_TEST_STRAT
		# Get wagman info
		data = self.collect_wagman_info()
		self.send('wagman info', data)
		#********** SH_TEST_END



		# Get whitelist
		whitelist = get_white_list()
		if 'error:' in whitelist:
			whitelist = []

		# Get auto start plugin list
		autoplugins = self.get_autostart_dict("/dev/")
		delete_plugins = []

		# notifier = Notifier(wm, PTmp())
		# wdd = wm.add_watch(path, mask, rec=True)
		while self.man[self.name]:

			# Check if predefined serial port is recognizable (sensor attached)
			# try:
			# 	notifier.process_events()
			# 	if notifier.check_events():
			# 		notifier.read_events()
			# except Exception as e:
			# 	notifier.stop()
			for device in autoplugins:
				plugin = autoplugins[device]
				# Check if the device is attached or not, based on device_rules in waggle_image
				if os.path.islink(device) or os.path.isfile(device):
					if plugin in whitelist:
						continue
					elif plugin == '':
						continue
					else:
						# Check if plugin alive
						cmd = "info %s" % (plugin)
						ret = self.send_command(cmd)
						if 'status' in ret and ret['status'] == 'success':
							continue
						else:
							# Start the plugin
							logger.debug("Try to start %s" % (plugin))
							cmd = "start %s" % (plugin)
							ret = self.send_command(cmd)
							if 'status' in ret and ret['status'] == 'success':
								logger.debug("%s is up and running" % (plugin))
								delete_plugins.append(device)
							else:
								logger.debug("%s failed to start" % (plugin))

			if delete_plugins:
				for device in delete_plugins:
					del autoplugins[device]
				delete_plugins = []


			time.sleep(3)
