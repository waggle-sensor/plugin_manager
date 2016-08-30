#!/usr/bin/env python3

'''
Alphasense reader using the USB-ISS interface. The only real dependency
is on the set_spi_mode and transfer_data functions. This could easily be
replaced with some other layer.

Example:

Suppose that the Alphasense is device /dev/ttyACM0. You can simply run:

python alphasense.py /dev/ttyACM0

USB-ISS Reference:
https://www.robot-electronics.co.uk/htm/usb_iss_tech.htm

Alphasense Reference:
waggle-sensor/waggle/docs/alphasense-opc-n2/
'''
from serial import Serial
from time import sleep
import struct
import sys
import logging


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def iss_spi_divisor(sck):
    divisor = (6000000 / sck) - 1

    if int(divisor) != divisor:
        raise ValueError('Nonintegral SCK divisor.')

    return int(divisor)


def iss_set_spi_mode(serial, mode, freq):
    serial.write(bytearray([0x5A, 0x02, mode, iss_spi_divisor(freq)]))
    response = serial.read(2)
    if response[0] == 0:
        if response[1] == 0x05:
            raise RuntimeError('USB-ISS: Unknown Command')
        elif response[1] == 0x06:
            raise RuntimeError('USB-ISS: Internal Error 1')
        elif response[1] == 0x07:
            raise RuntimeError('USB-ISS: Internal Error 2')
        else:
            raise RuntimeError('USB-ISS: Undocumented Error')


def iss_spi_transfer_data(serial, data):
    serial.write(bytearray([0x61] + data))
    response = bytearray(serial.read(1 + len(data)))
    if response[0] == 0:
        raise RuntimeError('USB-ISS: Transmission Error')
    return response


def decode17(data):
    bincounts = struct.unpack_from('<16H', data, offset=0)
    mtof = [x / 3 for x in struct.unpack_from('<4B', data, offset=32)]
    sample_flow_rate = struct.unpack_from('<f', data, offset=36)[0]
    pressure = struct.unpack_from('<I', data, offset=40)[0]
    temperature = pressure / 10.0
    sampling_period = struct.unpack_from('<f', data, offset=44)[0]
    checksum = struct.unpack_from('<H', data, offset=48)[0]
    pmvalues = struct.unpack_from('<3f', data, offset=50)

    assert pmvalues[0] <= pmvalues[1] <= pmvalues[2]

    values = {
        'bins': bincounts,
        'mtof': mtof,
        'sample flow rate': sample_flow_rate,
        'sampling period': sampling_period,
        'pm1': pmvalues[0],
        'pm2.5': pmvalues[1],
        'pm10': pmvalues[2],
        'error': sum(bincounts) & 0xFFFF != checksum,
    }

    if temperature > 200:
        values['pressure'] = pressure
    else:
        values['temperature'] = temperature

    return values


def unpack_structs(structs, data):
    results = {}

    offset = 0

    for key, fmt in structs:
        values = struct.unpack_from(fmt, data, offset)
        if len(values) == 1:
            results[key] = values[0]
        else:
            results[key] = values
        offset += struct.calcsize(fmt)

    return results


class Alphasense(object):

    bin_units = {
        'bins': 'particle / second',
        'mtof': 'second',
        'sample flow rate': 'sample / second',
        'pm1': 'microgram / meter^3',
        'pm2.5': 'microgram / meter^3',
        'pm10': 'microgram / meter^3',
        'temperature': 'celcius',
        'pressure': 'pascal',
    }

    histogram_data_struct = [
        ('bins', '<16H'),
        ('mtof', '<4B'),
        ('sample flow rate', '<f'),
        ('weather', '<f'),
        ('sampling period', '<f'),
        ('checksum', '<H'),
        ('pm1', '<f'),
        ('pm2.5', '<f'),
        ('pm10', '<f'),
    ]

    config_data_structs = [
        ('bin boundaries', '<16H'),
        ('bin particle volume', '<16f'),
        ('bin particle density', '<16f'),
        ('bin particle weighting', '<16f'),
        ('gain scaling coefficient', '<f'),
        ('sample flow rate', '<f'),
        ('laser dac', '<B'),
        ('fan dac', '<B'),
        ('tof to sfr factor', '<B'),
    ]

    def __init__(self, port):
        self.serial = Serial(port)
        iss_set_spi_mode(self.serial, 0x92, 500000)

    def close(self):
        self.serial.close()

    def transfer(self, data):
        result = bytearray(len(data))

        for i, x in enumerate(data):
            iss_result = iss_spi_transfer_data(self.serial, [x])
            if iss_result[0] != 0xFF:
                raise RuntimeError('USB-ISS Read Error')
            result[i] = iss_result[1]
            sleep(0.001)

        return result

    def power_on(self, fan=True, laser=True):
        if fan and laser:
            self.transfer([0x03, 0x00])
        elif fan:
            self.transfer([0x03, 0x04])
        elif laser:
            self.transfer([0x03, 0x02])

    def power_off(self, fan=True, laser=True):
        if fan and laser:
            self.transfer([0x03, 0x01])
        elif fan:
            self.transfer([0x03, 0x05])
        elif laser:
            self.transfer([0x03, 0x03])

    def set_laser_power(self, power):
        self.transfer([0x42, 0x01, power])

    def set_fan_power(self, power):
        self.transfer([0x42, 0x00, power])

    def get_firmware_version(self):
        self.transfer([0x3F])
        sleep(0.01)
        return self.transfer([0] * 60)

    def get_config_data_raw(self):
        self.transfer([0x3C])
        sleep(0.01)
        return self.transfer([0] * 256)

    def get_config_data(self):
        config_data = self.get_config_data_raw()
        return unpack_structs(self.config_data_structs, config_data)

    def ready(self):
        return self.transfer([0xCF])[0] == 0xF3

    def get_histogram_raw(self):
        self.transfer([0x30])
        sleep(0.01)
        return self.transfer([0] * 62)

    def get_histogram(self):
        return decode17(self.get_histogram_raw())

    def get_pm(self):
        self.transfer([0x32])
        sleep(0.01)
        data = self.transfer([0] * 12)
        return struct.unpack('<3f', data)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(('Usage: {} device-name'.format(sys.argv[0])))
        sys.exit(1)

    alphasense = Alphasense(sys.argv[1])
    sleep(3)

    version = alphasense.get_firmware_version()
    sleep(1)

    config = alphasense.get_config_data()
    sleep(1)

    alphasense.set_fan_power(255)
    sleep(1)

    alphasense.set_laser_power(190)
    sleep(1)

    alphasense.power_on()
    sleep(1)

    try:
        while True:
            sleep(10)

            rawdata = alphasense.get_histogram_raw()
            data = decode17(rawdata)

            if data['error']:
                raise RuntimeError('Alphasense histogram error.')

            print(data)
    finally:
        alphasense.close()
