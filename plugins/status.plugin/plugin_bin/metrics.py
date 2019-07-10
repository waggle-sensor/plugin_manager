from serial import Serial
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
        rx = int(read_file(os.path.join(
            '/sys/class/net', iface, 'statistics/rx_bytes')))
        tx = int(read_file(os.path.join(
            '/sys/class/net', iface, 'statistics/tx_bytes')))
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


def scan_wagman_log(metrics, log):
    metrics['wagman_comm'] = ':wagman:' in log

    try:
        nc, ep, cs = re.findall(r':fails (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_fc_nc'] = int(nc)
        metrics['wagman_fc_ep'] = int(ep)
        metrics['wagman_fc_cs'] = int(cs)
    except Exception:
        logger.exception('scan wagman fc failed')

    try:
        wm, nc, ep, cs = re.findall(r':cu (\d+) (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_cu_wm'] = int(wm)
        metrics['wagman_cu_nc'] = int(nc)
        metrics['wagman_cu_ep'] = int(ep)
        metrics['wagman_cu_cs'] = int(cs)
    except Exception:
        logger.exception('scan wagman cu failed')

    try:
        th = re.findall(r':th (\d+) (\d+) (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_th_0'] = int(th[0])
        metrics['wagman_th_1'] = int(th[1])
        metrics['wagman_th_2'] = int(th[2])
        metrics['wagman_th_3'] = int(th[3])
        metrics['wagman_th_4'] = int(th[4])
    except Exception:
        logger.exception('scan wagman th failed')

    try:
        value = re.findall(r':temperature\s+(\d+)\s+', log)[-1]
        metrics['wagman_temperature'] = int(value)
    except Exception:
        logger.exception('scan wagman temperature failed')

    try:
        value = re.findall(r':humidity\s+(\d+)\s+', log)[-1]
        metrics['wagman_humidity'] = int(value)
    except Exception:
        logger.exception('scan wagman humidity failed')

    try:
        value = re.findall(r':light (\d+)', log)[-1]
        metrics['wagman_light'] = int(value)
    except Exception:
        logger.exception('scan wagman light failed')

    try:
        nc, ep, cs = re.findall(r':enabled (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_enabled_nc'] = bool(nc)
        metrics['wagman_enabled_ep'] = bool(ep)
        metrics['wagman_enabled_cs'] = bool(cs)
    except Exception:
        logger.exception('scan wagman enabled failed')

    try:
        ports = re.findall(r':vdc (\d+) (\d+) (\d+) (\d+) (\d+)', log)[-1]
        metrics['wagman_vdc_nc'] = int(ports[0])
        metrics['wagman_vdc_ep'] = int(ports[1])
        metrics['wagman_vdc_cs'] = int(ports[2])
    except Exception:
        logger.exception('scan wagman voltage failed')

    try:
        metrics['wagman_hb_nc'] = 'nc heartbeat' in log
        metrics['wagman_hb_ep'] = 'gn heartbeat' in log
        metrics['wagman_hb_cs'] = 'cs heartbeat' in log
    except Exception:
        logger.exception('scan wagman heartbeat failed')

    metrics['wagman_stopping_nc'] = bool(re.search(r'wagman:nc stopping', log))
    metrics['wagman_stopping_ep'] = bool(re.search(r'wagman:gn stopping', log))
    metrics['wagman_stopping_cs'] = bool(re.search(r'wagman:cs stopping', log))

    metrics['wagman_starting_nc'] = bool(re.search(r'wagman:nc starting', log))
    metrics['wagman_starting_ep'] = bool(re.search(r'wagman:gn starting', log))
    metrics['wagman_starting_cs'] = bool(re.search(r'wagman:cs starting', log))

    metrics['wagman_killing_nc'] = bool(re.search(r'wagman:nc killing', log))
    metrics['wagman_killing_ep'] = bool(re.search(r'wagman:gn killing', log))
    metrics['wagman_killing_cs'] = bool(re.search(r'wagman:cs killing', log))


# HACK wagman_last_scan_time is used to track the last time we scanned the wagman logs
wagman_last_scan_time = time.monotonic()


def get_recent_wagman_log():
    global wagman_last_scan_time

    scan_duration = int(time.monotonic() - wagman_last_scan_time + 5)

    output = subprocess.check_output([
        'journalctl',                   # scan journal for
        '-u', 'waggle-wagman-driver',   # wagman driver logs
        # from last scan time
        '--since', '-{}'.format(scan_duration),
        '-b',                           # from this boot only
        '-o', 'cat',                    # in compact form
    ]).decode()

    wagman_last_scan_time = time.monotonic()

    return output


def get_wagman_metrics(config, metrics):
    # optimization... doesn't bother with query if device missing.
    if not get_dev_exists('/dev/waggle_sysmon'):
        return

    with suppress(Exception):
        metrics['wagman_uptime'] = int(
            subprocess.check_output(['wagman-client', 'up']).decode())

    scan_wagman_log(metrics, get_recent_wagman_log())


rssi_to_dbm = {
    2: -109,
    3: -107,
    4: -105,
    5: -103,
    6: -101,
    7: -99,
    8: -97,
    9: -95,
    10: -93,
    11: -91,
    12: -89,
    13: -87,
    14: -85,
    15: -83,
    16: -81,
    17: -79,
    18: -77,
    19: -75,
    20: -73,
    21: -71,
    22: -69,
    23: -67,
    24: -65,
    25: -63,
    26: -61,
    27: -59,
    28: -57,
    29: -55,
    30: -53,
}


def get_modem_strength(config, metrics):
    modems = glob('/dev/serial/by-id/*Telit*if06')

    if not modems:
        logger.warning('no modem detected - skipping')
        return

    with Serial(modems[0], 57600, timeout=1.0) as ser:
        ser.write(b'AT+CSQ\r')

        rssi = None

        while True:
            try:
                s = ser.readline().decode()
            except UnicodeDecodeError:
                continue

            if len(s) == 0:
                logger.warning('modem closed unexpectedly')
                return

            if s.startswith('OK'):
                break

            m = re.match(r'\+CSQ:\s*(\d+),(\d+)', s)

            if m is not None:
                rssi = int(m.group(1))

        try:
            dbm = rssi_to_dbm[rssi]
        except KeyError:
            logger.warning('unknown modem strength')
            return

        metrics['modem_dbm'] = dbm


def get_loadavg_metrics(config, metrics):
    s = read_file('/proc/loadavg')
    fs = s.split()
    metrics['loadavg1'] = float(fs[0])
    metrics['loadavg5'] = float(fs[1])
    metrics['loadavg15'] = float(fs[2])


def get_mem_metrics(config, metrics):
    s = read_file('/proc/meminfo')
    metrics['mem_total'] = int(
        re.search(r'MemTotal:\s*(\d+)\s*kB', s).group(1)) * 1024
    metrics['mem_free'] = int(
        re.search(r'MemFree:\s*(\d+)\s*kB', s).group(1)) * 1024
    metrics['mem_free_ratio'] = metrics['mem_free'] / metrics['mem_total']


def get_disk_metrics(config, metrics):
    size = {}
    used = {}

    for line in subprocess.check_output(['df']).decode().splitlines()[1:]:
        fs = line.split()
        mount = fs[5]
        size[mount] = int(fs[1]) * 1024  # df reports 1K blocks
        used[mount] = int(fs[2]) * 1024

    with suppress(KeyError):
        metrics['disk_size_boot'] = size['/media/boot']
        metrics['disk_used_boot'] = used['/media/boot']
        metrics['disk_used_ratio_boot'] = round(
            used['/media/boot'] / size['/media/boot'], 3)

    with suppress(KeyError):
        metrics['disk_size_root'] = size['/']
        metrics['disk_used_root'] = used['/']
        metrics['disk_used_ratio_root'] = round(used['/'] / size['/'], 3)

    with suppress(KeyError):
        metrics['disk_size_rw'] = size['/wagglerw']
        metrics['disk_used_rw'] = used['/wagglerw']
        metrics['disk_used_ratio_rw'] = round(
            used['/wagglerw'] / size['/wagglerw'], 3)


def get_plugin_metrics(config, metrics):
    try:
        plugins = [p for p in os.listdir(
            '/wagglerw/systemd/system') if p.startswith('waggle-plugin')]
    except FileNotFoundError:
        plugins = []

    active_total = 0

    for plugin in plugins:
        try:
            subprocess.check_output(['systemctl', 'is-active', plugin])
            active_total += 1
        except Exception:
            pass

    metrics['plugins_enabled'] = len(plugins)
    metrics['plugins_active'] = active_total


def get_sys_metrics(config, metrics):
    metrics['uptime'] = get_sys_uptime()
    metrics['time'] = int(time.time())
    get_loadavg_metrics(config, metrics)
    get_mem_metrics(config, metrics)
    get_disk_metrics(config, metrics)
    get_plugin_metrics(config, metrics)

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


def ping_sshmsg(host, port):
    try:
        s = socket.create_connection((host, port), timeout=10)
        s.settimeout(5)
        data = s.recv(32)
        s.close()
        return b'OpenSSH' in data
    except Exception:
        return False


def ping_ping(host):
    try:
        subprocess.check_output(['ping', '-c', '4', host])
        return True
    except Exception:
        return False


ping_table = {
    'beehive': (ping_sshmsg, 'beehive', 20022),
    'nc': (ping_ping, '10.31.81.10'),
    'ep': (ping_ping, '10.31.81.51'),
}


def get_ping_metrics(config, metrics):
    for name in config['ping']:
        if name not in ping_table:
            logger.warning('no ping host "%s"', name)
            continue

        method, *args = ping_table[name]
        metrics['ping_' + name] = method(*args)


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

        metrics['service_' + name] = get_service_status(service_table[name])


def attempt_to_get_metrics(getter, config, metrics):
    try:
        getter(config, metrics)
    except Exception:
        logger.exception('metrics getter failed %s', getter)


def get_metrics_for_config(config):
    metrics = {}

    attempt_to_get_metrics(get_sys_metrics, config, metrics)
    attempt_to_get_metrics(get_device_metrics, config, metrics)

    if 'wagman' in config['devices']:
        attempt_to_get_metrics(get_wagman_metrics, config, metrics)

    if 'modem' in config['devices']:
        attempt_to_get_metrics(get_modem_strength, config, metrics)

    attempt_to_get_metrics(get_ping_metrics, config, metrics)
    attempt_to_get_metrics(get_network_metrics, config, metrics)
    attempt_to_get_metrics(get_service_metrics, config, metrics)

    return metrics


def main():
    import pprint
    import sys
    config = read_config_file(sys.argv[1])
    metrics = get_metrics_for_config(config)
    pprint.pprint(metrics)


if __name__ == '__main__':
    main()
