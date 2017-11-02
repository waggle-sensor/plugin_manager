#! /usr/bin/env python3

import time
import os
import argparse
from serial import Serial, SerialException

from waggle.protocol import decode_frame, convert

device = os.environ.get('CORESENSE_DEVICE', '/dev/waggle_coresense')


class DeviceHandler(object):
    def __init__(self, device):
        self.serial = Serial(device, baudrate=115200, timeout=180)

        self.START_BYTE = 0xAA
        self.END_BYTE = 0x55
        self.HEADER_SIZE = 4
        self.HEADER_SIZE = 2

    def close(self):
        self.serial.close()

    def read_response(self):
        data = bytearray()
        while True:
            if self.serial.inWaiting() > 0:
                data.extend(self.serial.read(self.serial.inWaiting()))
                try:
                    del data[:data.index(self.START_BYTE)]
                except ValueError:
                    del data[:]

                if len(data) >= self.HEADER_SIZE:
                    packet_length = data[4]
                    if len(data) >= self.HEADER_SIZE + length + self.FOOTER_SIZE:
                        packet = data[:self.HEADER_SIZE + length + self.FOOTER_SIZE]
                        del data[:len(packet)]
                        return packet

            else:
                time.sleep(0.1)


    def request_data(self, sensors):
        if sensors == []:
            return None
        # Packaging
        buffer = bytearray()
        buffer.append(0xAA) # preamble
        buffer.append(0x02) # data type ( request )
        buffer.append(0x80) # sequence ( 0 )
        data = bytearray()
        for sensor in sensors:
            data.append(0x21)
            data.append(sensor)
        buffer.append(len(data))
        buffer.extend(data)
        buffer.append(0x00) # crc
        buffer.append(0x55) # postscript

        self.serial.write(bytes(buffer))

        return self.read_response()



class CoresensePlugin4(object):
    def __init__(self, input_handler, sensors, beehive=True, hrf=False):
        self.plugin_name = 'coresense'
        self.plugin_version = '4'
        self.sensors = sensors
        for sensor in self.sensors:
            s = self.sensors[sensor]
            s['last_updated'] = time.time()
            self.sensors[sensor] = s
        self.input_handler = input_handler
        self.beehive = beehive
        self.hrf = hrf

    def close(self):
        self.input_handler.close()

    def _get_requests(self):
        requests = []
        current_time = time.time()
        for sensor in self.sensors:
            s = self.sensors[sensor]
            if s['last_updated'] + s['interval'] < current_time:
                requests.append(s['sensor_id'])
                s['last_updated'] = current_time
                self.sensors[sensor] = s
        return requests

    def _print(packets, hrf=False):
        decoded = decode_frame(packets)
        print(decoded)

    def run(self):
        while True:
            # Blocking function
            message = self.input_handler.request_data(self._get_requests())
            if message not None:
                print('Error: Received None!')

            if self.beehive:
                pass
                # Send it to beehive
            elif self.hrf:
                _print(message, hrf=True)
                # Print in human readable form
            else:
                # Print received packet
                _print(message, hrf=False)

            time.sleep(0.5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--on-node', action='store_true', help='Run on node')
    parser.add_argument('--beehive', action='store_true', help='Report to Beehive')
    parser.add_argument('--hrf', action='store_true', help='Print in human readable form')
    args = parser.parse_args()

    sensor_table = {
        'MetMAC': { 'sensor_id': 0x00, 'interval': 3 },
        # 'TMP112': {'sensor_id': 0x01, 'interval': 1 },
    }

    handler = None
    if args.on_node:
        handler = DeviceHandler(device)
    else:
        parser.print_help()
        exit(1)

    plugin = CoresensePlugin4(handler, sensors=sensor_table, beehive=args.beehive, hrf=args.hrf)
    try:
        plugin.run()
    except KeyboardInterrupt:
        pass
    finally:
        plugin.close()

