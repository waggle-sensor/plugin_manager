import socket
import subprocess
import os
import re
import time
from contextlib import suppress
from glob import glob
import logging
import configparser


logger = logging.getLogger('metrics')


def read_file(path):
    logger.debug('read_file %s', path)
    with open(path) as file:
        return file.read()


def read_section_keys(config, section):
    try:
        return list(config[section])
    except KeyError:
        return []


def read_config_file(path):
    logger.debug('reading config %s', path)

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(path)

    return {
        'devices': read_section_keys(config, 'devices'),
        'network': read_section_keys(config, 'network'),
        'ping': read_section_keys(config, 'ping'),
        'services': read_section_keys(config, 'services'),
    }


def get_sys_uptime():
    fields = read_file('/proc/uptime').split()
    return int(float(fields[0]))


def get_dev_exists(path):
    return os.path.exists(path)


def get_net_metrics(iface):
    try:
        rx = int(read_file(os.path.join('/sys/class/net', iface, 'statistics/rx_bytes')))
        tx = int(read_file(os.path.join('/sys/class/net', iface, 'statistics/tx_bytes')))
    except FileNotFoundError:
        rx = 0
        tx = 0
    return rx, tx


def get_service_status(service):
    try:
        subprocess.check_output(['systemctl', 'is-active', service]).decode()
        return True
    except subprocess.CalledProcessError:
        return False


# can also have a log tail process watching all the wagman logs for events
# maybe include lookback time in config?
def get_wagman_metrics(config, metrics):
    # optimization... doesn't bother with query if device missing.
    if not get_dev_exists('/dev/waggle_sysmon'):
        return

    with suppress(Exception):
        metrics['wagman_uptime'] = int(subprocess.check_output(['wagman-client', 'up']).decode())

    log = subprocess.check_output([
        'journalctl',                   # scan journal for
        '-u', 'waggle-wagman-driver',   # wagman driver logs
        '--since', '-60',               # from last 60s
        '-b',                           # from this boot only
        '-o', 'cat',                    # in compact form
    ]).decode()

    metrics['wagman_comm'] = ':wagman:' in log

    with suppress(Exception):
        nc, ep, cs = re.findall(r':fails (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_fc_nc'] = int(nc)
        metrics['wagman_fc_ep'] = int(ep)
        metrics['wagman_fc_cs'] = int(cs)

    with suppress(Exception):
        wm, nc, ep, cs = re.findall(r':cu (\d+) (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_cu_wm'] = int(wm)
        metrics['wagman_cu_nc'] = int(nc)
        metrics['wagman_cu_ep'] = int(ep)
        metrics['wagman_cu_cs'] = int(cs)

    with suppress(Exception):
        th = re.findall(r':th (\d+) (\d+) (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_th_0'] = int(th[0])
        metrics['wagman_th_1'] = int(th[1])
        metrics['wagman_th_2'] = int(th[2])
        metrics['wagman_th_3'] = int(th[3])
        metrics['wagman_th_4'] = int(th[4])

    with suppress(Exception):
        nc, ep, cs = re.findall(r':enabled (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_enabled_nc'] = bool(nc)
        metrics['wagman_enabled_ep'] = bool(ep)
        metrics['wagman_enabled_cs'] = bool(cs)

    with suppress(Exception):
        ports = re.findall(r':vdc (\d+) (\d+) (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_vdc_nc'] = int(ports[0])
        metrics['wagman_vdc_ep'] = int(ports[1])
        metrics['wagman_vdc_cs'] = int(ports[2])

    with suppress(Exception):
        metrics['wagman_hb_nc'] = 'nc heartbeat' in log
        metrics['wagman_hb_ep'] = 'gn heartbeat' in log
        metrics['wagman_hb_cs'] = 'cs heartbeat' in log

    metrics['wagman_stopping_nc'] = bool(re.search(r'wagman:nc stopping', log))
    metrics['wagman_stopping_ep'] = bool(re.search(r'wagman:gn stopping', log))
    metrics['wagman_stopping_cs'] = bool(re.search(r'wagman:cs stopping', log))

    metrics['wagman_starting_nc'] = bool(re.search(r'wagman:nc starting', log))
    metrics['wagman_starting_ep'] = bool(re.search(r'wagman:gn starting', log))
    metrics['wagman_starting_cs'] = bool(re.search(r'wagman:cs starting', log))

    metrics['wagman_killing_nc'] = bool(re.search(r'wagman:nc killing', log))
    metrics['wagman_killing_ep'] = bool(re.search(r'wagman:gn killing', log))
    metrics['wagman_killing_cs'] = bool(re.search(r'wagman:cs killing', log))


def check_ping(args):
    host, port = args

    try:
        s = socket.create_connection((host, port), timeout=10)
        s.settimeout(5)
        data = s.recv(32)
        s.close()
        return b'OpenSSH' in data
    except Exception:
        return False


def get_loadavg_metrics(config, metrics):
    s = read_file('/proc/loadavg')
    fs = s.split()
    metrics['loadavg1'] = float(fs[0])
    metrics['loadavg5'] = float(fs[1])
    metrics['loadavg15'] = float(fs[2])


def get_mem_metrics(config, metrics):
    s = read_file('/proc/meminfo')
    metrics['mem_total'] = int(re.search(r'MemTotal:\s*(\d+)\s*kB', s).group(1)) * 1024
    metrics['mem_free'] = int(re.search(r'MemFree:\s*(\d+)\s*kB', s).group(1)) * 1024


def get_disk_metrics(config, metrics):
    size = {}
    used = {}

    for line in subprocess.check_output(['df']).decode().splitlines()[1:]:
        fs = line.split()
        mount = fs[5]
        size[mount] = int(fs[1]) * 1024
        used[mount] = int(fs[2])

    with suppress(KeyError):
        metrics['disk_used_boot'] = used['/media/boot']
        metrics['disk_size_boot'] = size['/media/boot']

    with suppress(KeyError):
        metrics['disk_used_root'] = used['/']
        metrics['disk_size_root'] = size['/']

    with suppress(KeyError):
        metrics['disk_used_rw'] = used['/wagglerw']
        metrics['disk_size_rw'] = size['/wagglerw']


def get_sys_metrics(config, metrics):
    metrics['uptime'] = get_sys_uptime()
    metrics['time'] = int(time.time())
    get_loadavg_metrics(config, metrics)
    get_mem_metrics(config, metrics)
    get_disk_metrics(config, metrics)

    hostname = subprocess.check_output(['hostname']).decode()
    if 'SD' in hostname:
        metrics['media'] = 0
    elif 'MMC' in hostname:
        metrics['media'] = 1



device_table = {
    'wagman': '/dev/waggle_sysmon',
    'coresense': '/dev/waggle_coresense',
    'modem': '/dev/attwwan',
    'wwan': '/sys/class/net/ppp0',
    'lan': '/sys/class/net/eth0',
    'mic': '/dev/waggle_microphone',
    'samba': '/dev/serial/by-id/usb-03eb_6124-if00',
    'bcam': '/dev/waggle_cam_bottom',
    'tcam': '/dev/waggle_cam_top',
}


def get_device_metrics(config, metrics):
    for name in config['devices']:
        if name not in device_table:
            logger.warning('no device "%s"', name)
            continue

        metrics['dev_up_' + name] = get_dev_exists(device_table[name])


ping_table = {
    'beehive': ('beehive', 20022),
    'nc': ('10.31.81.10', 22),
    'ep': ('10.31.81.51', 22),
}


def get_ping_metrics(config, metrics):
    for name in config['ping']:
        if name not in ping_table:
            logger.warning('no ping host "%s"', name)
            continue

        metrics['ping_' + name] = check_ping(ping_table[name])


network_table = {
    'wwan': 'ppp0',
    'lan': 'eth0',
}


def get_network_metrics(config, metrics):
    for name in config['network']:
        if name not in network_table:
            logger.warning('no network interface "%s"', name)
            continue

        rx, tx = get_net_metrics(network_table[name])
        metrics['net_rx_' + name] = rx
        metrics['net_tx_' + name] = tx


service_table = {
    'rabbitmq': 'rabbitmq-server',
    'coresense': 'waggle-plugin-coresense',
}

def get_service_metrics(config, metrics):
    for name in config['services']:
        if name not in service_table:
            logger.warning('no service "%s"', name)
            continue

        metrics['service_active_' + name] = get_service_status(service_table[name])


def get_metrics_for_config(config):
    metrics = {}

    get_sys_metrics(config, metrics)
    get_device_metrics(config, metrics)

    if 'wagman' in config['devices']:
        get_wagman_metrics(config, metrics)

    get_ping_metrics(config, metrics)
    get_network_metrics(config, metrics)
    get_service_metrics(config, metrics)

    return metrics


def main():
    import pprint
    import sys
    config = read_config_file(sys.argv[1])
    metrics = get_metrics_for_config(config)
    pprint.pprint(metrics)


if __name__ == '__main__':
    main()
