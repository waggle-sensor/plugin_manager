#!/usr/bin/env python3

"""
This module provides an interface to the Waggle coresense device. The Waggle
coresense devices show up as USB serial devices. For example, the device may
show us as '/dev/ttyACMX' on a Linux system.

In order to access the data provided by this device, we'll create a Connection
object provided by this module (or with the contextmanager create_connection).

>>> import coresense

>>> with coresense.create_connection('/dev/ttyACM0') as conn:
>>>     message = conn.recv()
>>>     for entry in message:
>>>         print(entry)

This will connect to the coresense device, receive a decoded message and then
print each of the sensor entries received.
"""
from serial import Serial, SerialException
from contextlib import contextmanager
import time
import math

from .RTlist import getRT


START_BYTE = b'\xaa'
END_BYTE = 0x55
HEADER_SIZE = 3
FOOTER_SIZE = 2


class Connection(object):
    """Provides a socket-like interface to a coresense device."""

    def __init__(self, device):
        self.serial = Serial(device, timeout=180)
        self.data = bytearray()

    def close(self):
        """Closes the connection to the device."""
        self.serial.close()

    def read(self, count):
        result = self.serial.read(count)
        if len(result) < count:
            raise SerialException("Did read less than expected (expected %d, got only %d), maybe timeout problem." % (count, len(result)))
        return result

    def recv(self):
        """Receives a list of sensor entries from the device."""
        data = self.recv_packet_data()

        timestamp = int(time.time())

        entries = []

        offset = 0

        while offset < len(data):
            identifier = data[offset]

            header = data[offset + 1]
            length = header & 0x7F
            valid = header & 0x80 != 0

            entry_data = data[offset+2:offset+2+length]

            if valid:
                entries.append(parse_sensor(identifier, entry_data))

            offset += 2 + length  # header + contents

        return Message(timestamp, entries)

    def recv_packet_data(self):
        """Receives raw packet data from the device."""
        failures = 0

        while True:
            # get more data from device
            if self.serial.inWaiting() > 0:
                self.data.extend(self.serial.read(self.serial.inWaiting()))

            # either align to possible packet or drop non-existent frame
            try:
                del self.data[:self.data.index(START_BYTE)]
            except ValueError:
                del self.data[:]

            # check if we have an entire, valid packet and then send it
            if len(self.data) >= HEADER_SIZE:
                length = self.data[2]
                if len(self.data) >= HEADER_SIZE + length + FOOTER_SIZE:
                    crc = self.data[HEADER_SIZE + length + 0]
                    end = self.data[HEADER_SIZE + length + 1]
                    body = bytes(self.data)[HEADER_SIZE:HEADER_SIZE + length]

                    self.data[0] = 0  # clear frame byte to allow other packets

                    if end == END_BYTE and crc == crc8(body):
                        return body

                    failures += 1

                    if failures >= 10:
                        raise NoPacketError(failures)
            # prevent consuming huge CPU recource
            time.sleep(0.2)


@contextmanager
def create_connection(device):
    """Yields a managed coresense connection."""
    conn = Connection(device)
    try:
        yield conn
    finally:
        conn.close()


class Message(object):
    """Contains a list of sensor entries."""

    def __init__(self, timestamp, entries):
        self.timestamp = timestamp
        self.entries = entries

    def __repr__(self):
        return '[{} : {}]'.format(self.timestamp, self.entries)


class MessageEntry(object):
    """Contains information about a particular sensor from a packet."""

    def __init__(self, sensor, values):
        self.sensor = sensor
        self.values = values

    def __repr__(self):
        values_string = '; '.join('{}: {}'.format(name, value)
                                  for name, value in self.values)
        return '<{} | {}>'.format(self.sensor, values_string)


class NoPacketError(Exception):

    def __init__(self, attempts):
        self.attempts = attempts

    def __str__(self):
        return 'No packet received after {} attempts.'.format(self.attempts)


class UnknownSensorError(Exception):

    def __init__(self, identifier):
        self.identifier = identifier

    def __str__(self):
        return 'Unknown sensor ID {}.'.format(self.identifier)


def crc8(data, crc=0):
    for i in range(len(data)):
        crc ^= data[i]
        for j in range(8):
            if crc & 1 != 0:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc


def uint16(input):
    'unsigned 16-bit integer'
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2
    return value

uint16.length = 2


def int16(input):
    'signed 16-bit integer'
    byte1 = input[0]
    byte2 = input[1]
    value = ((byte1 & 0x7F) << 8) | byte2
    return value if byte1 & 0x80 == 0 else -value

int16.length = 2


def uint24(input):
    'unsigned 24-bit integer'
    byte1 = input[0]
    byte2 = input[1]
    byte3 = input[2]
    value = (byte1 << 16) | (byte2 << 8) | (byte3)
    return value

uint24.length = 3


def int24(input):
    'signed 24-bit integer'
    byte1 = input[0]
    byte2 = input[1]
    byte3 = input[2]
    value = ((byte1 & 0x7F) << 16) | (byte2 << 8) | (byte3)
    return value if byte1 & 0x80 == 0 else -value

int24.length = 3


def ufloat(input):
    byte1 = input[0]
    byte2 = input[1]
    # have to be careful here, we do not want three decimal placed here.
    value = (byte1 & 0x7F) + (((byte2 & 0x7F) % 100) * 0.01)
    if (byte1 & 0x80) == 0x80:
        value = value * -1
    return value

ufloat.length = 2


def lfloat(input):
    byte1 = input[0]
    byte2 = input[1]
    value = ((byte1 & 0x7c) >> 2) + ((((byte1 & 0x03) << 8) | byte2) * 0.001)
    if byte1 & 0x80 != 0:
        value = value * -1
    return value

lfloat.length = 2


def macaddr(input):
    return ''.join(['{:02X}'.format(b) for b in input])
    # return ''.join([str(format3(byte)) for byte in input])

macaddr.length = 6


def uint8array(input):
    'unsigned 8-bit integer[4]'
    # F7 - byte input[4], {0-0xffffffff} - Byte1 Byte2 Byte3 Byte4
    byte1 = input[0]
    byte2 = input[1]
    byte3 = input[2]
    byte4 = input[3]
    return [byte1, byte2, byte3, byte4]

uint8array.length = 4

def HIH4030_humidity(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    HIH4030_voltage = (value * 5.00) / 1023.00
    HIH4030_Humidity = (HIH4030_voltage - 0.85) * 100.00 / 3.00 # PUT DARK LEVEL VOLTAGE 0.85 FOR NOW
    return HIH4030_Humidity

HIH4030_humidity.length = 2

def PR103J2_temperature(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    temperature_PR = getRT(value)
    return temperature_PR

PR103J2_temperature.length = 2

def HMC5883L_mag_field(input):
    byte1 = input[0]
    byte2 = input[1]
    value = ((byte1 & 0x7c) >> 2) + ((((byte1 & 0x03) << 8) | byte2) * 0.001)
    if byte1 & 0x80 != 0:
        value = value * -1

    value = value * 10
    return value

HMC5883L_mag_field.length = 2

def TSL250RD_VL_analogRead(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    voltage = (value * 5.00) / 1023.00
    irradiance = (voltage - 0.09) / 0.064
    return irradiance

TSL250RD_VL_analogRead.length = 2

def TSL250RD_VL(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    voltage = ((value / 32768.00) * 2.048 * 5.00) / 2.00
    irradiance = (voltage - 0.09) / 0.064
    return irradiance

TSL250RD_VL.length = 2

def TSL260RD_IR(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    voltage = ((value / 32768.00) * 2.048 * 5.00) / 2.00
    irradiance = (voltage - 0.01) / 0.058
    return irradiance

TSL260RD_IR.length = 2

def APDS_AL(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    voltage = ((value / 32768.00) * 2.048 * 5.00) / 2.00
    irradiance = (voltage / 0.005 - 0.000156) * 2.5
    return irradiance

APDS_AL.length = 2

def MLX75305_AL(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    voltage = ((value / 32768.00) * 2.048 * 5.00) / 2.00
    irradiance = (voltage - 0.0996) / 0.007
    return irradiance

MLX75305_AL.length = 2
    

def ML8511_UV(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    voltage = ((value / 32768.00) * 2.048 * 5.00) / 2.00
    UV_index = (voltage - 1.489) / 1.4996 # initial value of voltage difference between when 1 mW/m^2 irradiates and dark condition

    if 2.5 <= UV_index <= 3.0:
        UV_index = UV_index - 0.3
    elif 3.0 <= UV_index <= 4.0:
        UV_index = UV_index - 0.6
    elif 4.0 <= UV_index <= 4.2:
        UV_index = UV_index - 0.4
    elif 4.5 < UV_index:
        UV_index = UV_index + 0.25

    return UV_index

ML8511_UV.length = 2

def divide_by_100(input):
    byte1 = input[0]
    byte2 = input[1]
    value = ((byte1 & 0x7F) << 8) | byte2

    if byte1 & 0x80 != 0:
        value = -value

    ADC_temp = value / 100.00
    return ADC_temp

divide_by_100.length = 2

def SPV_air(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2

    V_0 = value * 5.00 / 1023.00         # raw voltage of TSL
    V_I = (V_0 - 1.75) / 453.33 - 1.75   # raw voltage of SPV
    ############################################################################ Right till here
    voltage_level = -math.log10(-V_I / 3.3) * 20.00 # sound lever in dB
    return voltage_level

SPV_air.length = 2

def SPV_light(input):
    byte1 = input[0]
    byte2 = input[1]
    value = (byte1 << 8) | byte2
    
    raw_out = value / 32768.0000 * 2.048
    voltage = raw_out * 5.00 / 2.00
    voltage_level = -math.log10(voltage/3.3) * 20.00

SPV_light.length = 2

def sensor17(input):
    return string6(input[::2])

sensor17.length = -1


sensor_table = {
    0x00: ('Board MAC', [('MAC Address', macaddr)]),
    0x01: ('TMP112', [('Temperature', ufloat)]),
    0x02: ('HTU21D', [('Temperature', ufloat),
                      ('Humidity', ufloat)]),
    0x03: ('GP2Y1010AU0F', [('Dust', int24)]),                 # NOT IN ANY
    0x03: ('HIH4030', [('Humidity', HIH4030_humidity)]),       # NOT IN V2
    0x04: ('BMP180', [('Temperature', ufloat),
                      ('Pressure', int24)]),
    0x05: ('PR103J2', [('Temperature', PR103J2_temperature)]),
    0x06: ('TSL250RD', [('Light', TSL250RD_VL_analogRead)]),
    0x07: ('MMA8452Q', [('Accel X', ufloat),
                        ('Accel Y', ufloat),
                        ('Accel Z', ufloat),
                        ('RMS', ufloat)]),
    0x08: ('SPV1840LR5H-B', [('Sound level', SPV_air)]),
    0x09: ('TSYS01', [('Temperature', ufloat)]),

    0x0A: ('HMC5883L', [('B Field X', HMC5883L_mag_field),
                        ('B Field Y', HMC5883L_mag_field),
                        ('B Field Z', HMC5883L_mag_field)]),
    0x0B: ('HIH6130', [('Temperature', ufloat),
                       ('Humidity', ufloat)]),
    0x0C: ('APDS-9006-020', [('Light_LUX', APDS_AL)]),
    0x0D: ('TSL260RD', [('Light', TSL260RD_IR)]),
    0x0E: ('TSL250RD', [('Light', TSL250RD_VL)]),
    0x0F: ('MLX75305', [('Light', MLX75305_AL)]),
    0x10: ('ML8511', [('UV_index', ML8511_UV)]),
    0x11: ('D6T', [('Temperatures', sensor17)]),               # NOT IN ANY
    0x12: ('MLX90614', [('Temperature', ufloat)]),             # NOT IN ANY
    0x13: ('TMP421', [('Temperature', ufloat)]),
    0x14: ('SPV1840LR5H-B', [('Sound level', SPV_light)]),     # NOT IN V3

    0x15: ('Total reducing gases', [('Concentration', int24)]),
    0x16: ('Ethanol (C2H5-OH)', [('Concentration', int24)]),   # NOT IN ANY
    0x17: ('Nitrogen Di-oxide (NO2)', [('Concentration', int24)]),
    0x18: ('Ozone (03)', [('Concentration', int24)]),
    0x19: ('Hydrogen Sulphide (H2S)', [('Concentration', int24)]),
    0x1A: ('Total Oxidizing gases', [('Concentration', int24)]),
    0x1B: ('Carbon Monoxide (C0)', [('Concentration', int24)]),
    0x1C: ('Sulfur Dioxide (SO2)', [('Concentration', int24)]),
    0x1D: ('SHT25', [('Temperature', divide_by_100),
                     ('Humidity', divide_by_100)]),
    0x1E: ('LPS25H', [('Temperature', divide_by_100),
                      ('Pressure', uint24)]),
    0x1F: ('Si1145', [('Light', uint16),
                      ('Light', uint16),
                      ('Light', uint16)]),
    0x20: ('Intel MAC', [('MAC Address', macaddr)]),
    0x21: ('CO ADC Temp', [('ADC Temperature', divide_by_100)]),
    0x22: ('IAQ/IRR Temp', [('ADC Temperature', divide_by_100)]),
    0x23: ('O3/NO2 Temp', [('ADC Temperature', divide_by_100)]),
    0x24: ('SO2/H2S Temp', [('ADC Temperature', divide_by_100)]),
    0x25: ('CO LMP Temp', [('ADC Temperature', divide_by_100)]),
    0x26: ('Accelerometer', [('Accel X', int16),
                             ('Accel Y', int16),
                             ('Accel Z', int16),
                             ('Vib Index', uint24)]),
    0x27: ('Gyro', [('Orientation X', int16),
                    ('Orientation Y', int16),
                    ('Orientation Z', int16),
                    ('Orientation Index', uint24)]),
    0xFE: ('Sensor Health', [('Status', uint8array)])
}


def sensor_format_slices(formats):
    '''
    Yields the sensor data slices start:end for a list of sensor data formats.

    For example, if fmt1 has length 3 and fmt2 has length 4, then this
    function will yield slices 0:3 and 3:7.

    It also allows for a `tail` slices when a negative length is reached. In
    this case, the format will be applied to the tail of the sensor data.
    '''
    start = 0

    for name, fmt in formats:
        yield name, fmt, start, start + fmt.length
        start += fmt.length


def unpack_sensor_data(sensor_format, sensor_data):
    return [fmt(sensor_data[start:end])
            for name, fmt, start, end in sensor_format_slices(sensor_format)]


def parse_sensor(identifier, sensor_data):
    if identifier not in sensor_table:
        raise UnknownSensorError(identifier)

    entry_sensor, sensor_format = sensor_table[identifier]
    entry_values = unpack_sensor_data(sensor_format, sensor_data)
    entry_names = [name for name, _ in sensor_format]

    return MessageEntry(entry_sensor, list(zip(entry_names, entry_values)))

if __name__ == "__main__":
    with create_connection('/dev/ttyACM0') as conn:
        message = conn.recv()
        for entry in message.entries:
            print(entry)
