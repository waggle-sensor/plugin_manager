#!/usr/bin/env python3

import os, psutil, subprocess, datetime, time
from collections import namedtuple

"""
	This plugin is to monitor and report systematic information and activities vary from temperature, disk space, and system information to status of plugins.
	This plugin also detects USB devices to launch corresponding plugin.
"""

#TODO: when exceptions happen it could send an error code corresponding to the error, not sending the heavy error message, to reduce payload of the message. 

logger = logging.getLogger(__name__)

class register(object):
	def __init__(self, name, man, mailbox_outgoing):
		man[name] = 1
		base = base_plugin(name, man, mailbox_outgoing)
		base.run()

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
	list = ""
	if os.path.isfile(whitelist_file):
		try:
			with open(whitelist_file, 'r') as f:
				for line in f:
					if line.strip():
						list = list + "/" + line
		except Exception as e:
			list = "file read error: %s" % (str(e))
	else:
		list = "does not exist"

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

class base_plugin(object):
	plugin_name = 'base plugin'
	plugin_version = "1"
	def __init__(self, name, man, mailbox_outgoing):
		self.name = name
		self.man = man
		self.outqueue = mailbox_outgoing
		self.tmp = True

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

	def collect_system_info(self):
		data = {}
		data['disk'] = disk_usage("/")
		data['host name'] = get_host_name()
		data['reboots'] = get_boot_info(3)
		data['temperature'] = get_current_cpu_temp()

		return ['{}:{}'.format(keys, a[keys]).encode('iso-8859-1') for keys in data]

	def collect_service_info(self):
		data = {}
		data['whitelist'] = get_white_list()
		data['services'] = get_service_list()

		return ['{}:{}'.format(keys, a[keys]).encode('iso-8859-1') for keys in data]

	def collect_plugin_info(self):
		data = {}

		return ['{}:{}'.format(keys, a[keys]).encode('iso-8859-1') for keys in data]

	def run(self):
		# Wait a minute for other services preparing to run
		# TODO: need to know when all system/services are green so this report can send right information of the current system status.
		time.sleep(60)

		while self.man[self.name]:
			if self.tmp == True:
				self.tmp = False
				
				self.send('system info', collect_system_info())

				self.send('service info', collect_service_info())
			time.sleep(5)
