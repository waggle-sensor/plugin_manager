#! /usr/bin/env python3

import time
import os
import argparse
from serial import Serial, SerialException

from waggle.pipeline import Plugin
from waggle.protocol.v5.decoder import decode_frame, convert, check_crc, create_crc

import json

device = os.environ.get('CORESENSE_DEVICE', '/dev/waggle_coresense')

def get_default_configuration():
    sensor_table = {
        'MetMAC': { 'sensor_id': 0x00, 'function_call': 'sensor_read', 'interval': 25 },
        'TMP112': { 'sensor_id': 0x01, 'function_call': 'sensor_read', 'interval': 25 },
        'HTU21D': { 'sensor_id': 0x02, 'function_call': 'sensor_read', 'interval': 25 },
        'HIH4030': { 'sensor_id': 0x03, 'function_call': 'sensor_read', 'interval': 25 },
        'BMP180': { 'sensor_id': 0x04, 'function_call': 'sensor_read', 'interval': 25 },
        'PR103J2': { 'sensor_id': 0x05, 'function_call': 'sensor_read', 'interval': 25 },
        'TSL250RDMS': { 'sensor_id': 0x06, 'function_call': 'sensor_read', 'interval': 25 },
        'MMA8452Q': { 'sensor_id': 0x07, 'function_call': 'sensor_read', 'interval': 25 },
        'SPV1840LR5H-B': { 'sensor_id': 0x08, 'function_call': 'sensor_read', 'interval': 25 },
        'TSYS01': { 'sensor_id': 0x09, 'function_call': 'sensor_read', 'interval': 25 },

        'HMC5883L': { 'sensor_id': 0x0A, 'function_call': 'sensor_read', 'interval': 25 },
        'HIH6130': { 'sensor_id': 0x0B, 'function_call': 'sensor_read', 'interval': 25 },
        'APDS_9006_020': { 'sensor_id':0x0C, 'function_call': 'sensor_read', 'interval': 25 },
        'TSL260': { 'sensor_id': 0x0D, 'function_call': 'sensor_read', 'interval': 25 },
        'TSL250RDLS': { 'sensor_id': 0x0E, 'function_call': 'sensor_read', 'interval': 25 },
        'MLX75305': { 'sensor_id': 0x0F, 'function_call': 'sensor_read', 'interval': 25 },
        'ML8511': { 'sensor_id': 0x10, 'function_call': 'sensor_read', 'interval': 25 },
        'TMP421': { 'sensor_id': 0x13, 'function_call': 'sensor_read', 'interval': 25 },

        'Chemsense': { 'sensor_id': 0x2A, 'function_call': 'sensor_read', 'interval': 25 },

        'AlphaHisto': { 'sensor_id': 0x28, 'function_call': 'sensor_read', 'interval': 25 }, 
    }
    return sensor_table

class DeviceHandler(object):
    def __init__(self, device):
        self.serial = Serial(device, baudrate=115200, timeout=180)

        self.START_BYTE = 0xAA
        self.END_BYTE = 0x55
        self.HEADER_SIZE = 3
        self.FOOTER_SIZE = 2
        self.SQN = 0

    def close(self):
        self.serial.close()

    def read_response(self, timeout=180):
        data = bytearray()
        packets = bytearray()

        # The response must be received within 3 minutes
        for i in range(timeout * 2):
            if self.serial.inWaiting() > 0 or len(data) > 0:
                data.extend(self.serial.read(self.serial.inWaiting()))
                
                while True:
                    try:
                        del data[:data.index(self.START_BYTE)]
                    except ValueError:
                        del data[:]

                    if len(data) >= self.HEADER_SIZE:
                        packet_length = data[2]
                        if len(data) >= self.HEADER_SIZE + packet_length + self.FOOTER_SIZE:
                            packet = data[:self.HEADER_SIZE + packet_length + self.FOOTER_SIZE]
                            crc = packet[-2]
                            if not check_crc(crc, packet[self.HEADER_SIZE:-2]):
                                return None
                            sequence = data[3]
                            packets.extend(packet)
                            del data[:len(packet)]
                            if (sequence & 0x80) == 0x80:
                                return packets
                    else:
                        break
            else:
                time.sleep(0.5)

        # TIMEOUT: return packet that have been received
        return packets


    def request_data(self, sensors):
        # Packaging
        buffer = bytearray()
        buffer.append(0xAA) # preamble
        buffer.append(0x02) # data type (request) | protocol version (2)
        buffer.append(len(buffer))
        third_byte = 0x80 | self.SQN
        if self.SQN < 0x7F:
            self.SQN += 1
        else:
            self.SQN = 0
        buffer.append(third_byte) # sequence ( 0 )

        data = bytearray()
        while (len(sensors) != 0):
            if sensors[0] <= 0x06:
                data.append(sensors[0])   # function type
                data.append(0x01)
                data.append(sensors[1])   # sensor id
                sensors = sensors[2::]
            elif sensors[0] >= 0x11 and sensors[0] <= 0x16:
                data.append(sensors[0])   # function type
                data.append(sensors[1])   # bus type
                data.append(sensors[2])   # bus address
                data.extend(sensors[3:sensors[1] + 2])   # parameters
                sensors = sensors[sensors[1] + 2::]
        buffer.extend(data)

        buffer[2] = len(data) + 1
        buffer.append(create_crc(buffer[3:])) # crc
        buffer.append(0x55) # postscript
        self.serial.write(bytes(buffer))
        return self.read_response()


class CoresensePlugin4(Plugin):
    plugin_name = 'coresense'
    plugin_version = '4'

    def __init__(self, hrf=False):
        super().__init__()
        self.sensors = self._get_config_table()
        for sensor in self.sensors:
            s = self.sensors[sensor]
            s['last_updated'] = time.time()
            self.sensors[sensor] = s
        self.input_handler = DeviceHandler(device)
        self.hrf = hrf

        self.function_type = {
            'sensor_init': 1,
            'sensor_config': 2,
            'sensor_enable': 3,
            'sensor_diable': 4,
            'sensor_read': 5,
            'sensor_write': 6,
            'bus_init': 17,
            'bus_config': 18,
            'bus_enable': 19,
            'bus_disable': 20,
            'bus_read': 21,
            'bus_write': 22
        }
        self.bus_type = {
            0: 'i2c',
            1: 'spi',
            2: 'serial',
            3: 'analog',
            4: 'digital',
            5: 'pwm'
        }

    def close(self):
        self.input_handler.close()

    def _get_config_table(self):
        sensor_config_file = '/wagglerw/waggle/sensor_table.conf'
        sensor_table = None
        try:
            with open(sensor_config_file) as config:
                sensor_table = json.loads(config.read())
        except:
            sensor_table = get_default_configuration()
            with open(sensor_config_file, 'w') as config:
                config.write(json.dumps(sensor_table))

        return sensor_table

    def _get_requests(self):
        requests = []
        current_time = time.time()
        for sensor in self.sensors:
            s = self.sensors[sensor]
            if s['last_updated'] + s['interval'] < current_time:
                function_call_type = self.function_type[s['function_call']]
                requests.append(function_call_type)
                if (function_call_type <= 0x06):
                    requests.append(s['sensor_id'])
                elif (function_call_type >= 0x11 and function_call_type <= 0x16):
                    length_buffer = []
                    length_buffer.append(self.bus_type[s['bus_type']])
                    length_buffer.append(s['bus_address'])
                    length_buffer.extend(s['params'])
                    requests.append(len(length_buffer))
                    requests.extend(length_buffer)

                s['last_updated'] = current_time
                self.sensors[sensor] = s
        return requests

    def _print(self, packets):
        decoded = decode_frame(packets)

        if isinstance(decoded, dict):
            for item in decoded:
                converted_value = convert(decoded[item], item)
                print(converted_value)

        else:
            print('Error: Could not decode the packet %s' % (str(decoded),))


    def run(self):
        # Check firmware version and print
        try:
            check_firmware_request = [5, 255] # sensor_read, 0xFF
            message = self.input_handler.request_data(requests)
            if message is None:
                raise Exception('Version is null')
            else:
                if self.hrf:
                    self._print(message)
                else:
                    self.send(sensor='frame', data=message)
        except SerialException:
            print('Could not check firmware version due to serial error. Restarting...')
            return
        except Exception as ex:
            print('Could not check firmware version %s' % (str(ex),))
            return

        while True:
            requests = self._get_requests()
            if len(requests) > 0:
                try:
                    message = self.input_handler.request_data(requests)
                except SerialException:
                    print('Error in serial connection. Restarting...')
                    break

                if message is None:
                    print('Errors or invalid crc')
                    time.sleep(5)
                else:
                    print('Received frame')
                    if self.hrf:
                        self._print(message)
                    else:
                        self.send(sensor='frame', data=message)
            else:
                time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-sensor', action='store_true', help='Data from the sensor board')
    parser.add_argument('--hrf', action='store_true', help='Print in human readable form')
    args = parser.parse_args()

    if args.input_sensor:
        if not os.path.exists(device):
            exit(1)

        if args.hrf:
            plugin = CoresensePlugin4(hrf=args.hrf)
        else:
            plugin = CoresensePlugin4.defaultConfig()
        try:
            plugin.run()
        except (KeyboardInterrupt, Exception):
            pass
        finally:
            plugin.close()
    else:
        parser.print_help()