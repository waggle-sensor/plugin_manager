#!/usr/bin/env python3

import os
import json
import signal
import time
import datetime
from threading import Thread

import pika

graceful_signal_to_kill = False

EXCHANGE = 'image_pipeline'
ROUTING_KEY_EXPORT = 'exporter'


def get_default_configuration():
    conf = {
        'top': {
            'daytime': [('12:00:00', '23:00:00')],  # 6 AM to 7 PM in Chicago
            'interval': 3600,                       # every 60 mins
        },
        'bottom': {
            'daytime': [('12:00:00', '23:00:00')],  # 6 AM to 7 PM in Chicago
            'interval': 1800,                       # every 30 mins
        }
    }
    return conf


def get_config():
    config_file = '/wagglerw/waggle/image_collector.conf'
    config = None
    try:
        with open(config_file) as config_file:
            config = json.loads(config_file.read())
    except Exception:
        config = get_default_configuration()
        with open(config_file, 'w') as config_file:
            config_file.write(json.dumps(config, sort_keys=True, indent=4))

    return config


def get_daytime_durations(config_daytime):
    result = []
    try:
        for daytime_start, daytime_end in config_daytime:
            start_sp = daytime_start.strip().split(':')
            end_sp = daytime_end.strip().split(':')
            daytime_start = datetime.time(
                hour=int(start_sp[0]),
                minute=int(start_sp[1]),
                second=int(start_sp[2]))
            daytime_end = datetime.time(
                hour=int(end_sp[0]),
                minute=int(end_sp[1]),
                second=int(end_sp[2]))
            result.append((daytime_start, daytime_end))
    except Exception as ex:
        result = None
    return result


class ImageCollectionWorker(Thread):
    def __init__(self, device, daytime, interval):
        Thread.__init__(self)
        self.device_name = device
        self.routing_key = device
        self.stop_signal = False
        self.daytime = daytime
        self.interval = interval
        self.connection = None
        self.channel = None
        self.frame = None
        self.frame_headers = None

    def _close_connection(self):
        if self.connection is not None:
            if self.connection.is_open:
                self.connection.close()

    def _callback_read(self, ch, method, properties, body):
        self.frame = body
        self.frame_headers = properties.headers
        ch.stop_consuming()

    def close(self):
        self.stop_signal = True

    def open(self):
        parameters = pika.ConnectionParameters(
            host='localhost',
            connection_attempts=3,
            retry_delay=5,
            socket_timeout=2
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.queue = self.channel.queue_declare(exclusive=True, arguments={'x-max-length': 1}).method.queue
        self.channel.queue_bind(queue=self.queue, exchange=EXCHANGE, routing_key=self.routing_key)

    def read(self, timeout=30):
        for i in range(timeout):
            method, properties, body = self.channel.basic_get(queue=self.queue, no_ack=True)
            if method is not None:
                return True, (properties, body)
            time.sleep(0.1)
        return False, ''

    def write(self, frame, headers):
        properties = pika.BasicProperties(
            headers=headers,
            delivery_mode=2,
            timestamp=int(time.time() * 1000),
            content_type='b',
        )
        try:
            self.channel.basic_publish(
                properties=properties,
                exchange=EXCHANGE,
                routing_key=ROUTING_KEY_EXPORT,
                body=frame
            )
        except Exception as ex:
            return False, str(ex)
        return True, ''

    def check_daytime(self, current_time):
        time_now = datetime.datetime.fromtimestamp(current_time).time()
        time_start = time_end = None
        for start, end in self.daytime:
            time_start = time_now.replace(hour=start.hour, minute=start.minute, second=start.second)
            time_end = time_now.replace(hour=end.hour, minute=end.minute, second=end.second)
            if time_start <= time_now <= time_end:
                return True, 0
            elif time_start > time_now:
                return False, int((time_start - time_now).total_seconds())
        end_of_today = time_now.replace(hour=23, minute=59, second=59)
        return False, int((end_of_today - time_now).total_seconds())

    def run(self):
        print('Collection starts for %s' % (self.device_name,))
        try:
            self.open()
        except Exception as ex:
            print('Could not open connection to pipeline: %s' % (str(ex),))
            return

        last_updated = time.time() - (self.interval + 10)

        while not self.stop_signal:
            try:
                current_time = time.time()

                if current_time - last_updated > self.interval:
                    result, wait_time = self.check_daytime(current_time)
                    if result:
                        f, msg = self.read()
                        if f:
                            properties, frame = msg
                            properties.headers.update({'processing_software': os.path.basename(__file__)})
                            _f, _msg = self.write(frame, properties.headers)
                            if _f:
                                last_updated = current_time
                                print('An image from %s has been published' % (self.device_name,))
                            else:
                                print('Failed to publish for %s; %s' % (self.device_name, _msg))
                    else:
                        last_updated = current_time + min(wait_time, self.interval)
                time.sleep(1)
            except (KeyboardInterrupt, Exception) as ex:
                print(str(ex))
                break
        print('Collection ended for %s' % (self.device_name,))


def main():
    global graceful_signal_to_kill
    config = get_config()
    for device in config:
        try:
            device_config = config[device]
            daytime_durations = get_daytime_durations(device_config['daytime'])
            interval = int(device_config['interval'])
            device_config['daytime'] = daytime_durations
            device_config['interval'] = interval
            config[device] = device_config
        except Exception as ex:
            device_config = get_default_configuration()[device]
            daytime_durations = get_daytime_durations(device_config['daytime'])
            interval = int(device_config['interval'])
            device_config['daytime'] = daytime_durations
            device_config['interval'] = interval
            config[device] = device_config
            print('Could not load config properly fo %s. Use default.' % (device,))

    workers = []
    for device in config:
        device_config = config[device]

        worker = ImageCollectionWorker(
            device,
            device_config['daytime'],
            device_config['interval']
        )
        worker.start()
        workers.append(worker)

    try:
        while not graceful_signal_to_kill:
            for worker in workers:
                if not worker.is_alive():
                    print('Worker %s is not alive. Restarting...' % (worker.device_name,))
                    graceful_signal_to_kill = True
            time.sleep(1)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        for worker in workers:
            worker.stop_signal = True
            worker.join()


def sigterm_handler(signum, frame):
    global graceful_signal_to_kill
    graceful_signal_to_kill = True


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, sigterm_handler)
    main()
