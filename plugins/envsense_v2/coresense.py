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
from serial import Serial
from contextlib import contextmanager
import datetime


START_BYTE = 0xAA
END_BYTE = 0x55


class Connection(object):
    'Provides a socket-like interface to a coresense device.'

    def __init__(self, device):
        self.serial = Serial(device)

    def close(self):
        'Closes the connection to the device.'
        self.serial.close()

    def recv(self):
        'Receives a list of sensor entries from the device.'
        data = self.recv_packet_data()

        timestamp = datetime.datetime.now()
        entries = []

        offset = 0

        while offset < len(data):
            identifier = ord(data[offset])

            header = ord(data[offset + 1])
            length = header & 0x7F
            valid = header & 0x80 != 0

            entry_data = data[offset+2:offset+2+length]

            if valid:
                entries.append(parse_sensor(identifier, entry_data))

            offset += 2 + length  # header + contents

        return Message(timestamp, entries)

    def recv_packet_data(self):
        'Receives raw packet data from the device.'
        for attempt in range(10):

            # align stream to (possible) start of packet
            while ord(self.serial.read(1)) != START_BYTE:
                pass

            header = self.serial.read(2)
            length = ord(header[1])

            data = self.serial.read(length)

            footer = self.serial.read(2)
            crc = ord(footer[0])
            end = ord(footer[1])

            if end == END_BYTE and crc8(data) == crc:
                return data
        else:
            raise NoPacketError(attempt)


@contextmanager
def create_connection(device, version='2'):
    'Yields a managed coresense connection.'
    conn = Connection(device)
    try:
        yield conn
    finally:
        conn.close()


class Message(object):
    'Contains a list of sensor entries.'

    def __init__(self, timestamp, entries):
        self.timestamp = timestamp
        self.entries = entries

    def __repr__(self):
        return '[{} : {}]'.format(self.timestamp, self.entries)


class MessageEntry(object):
    'Contains information about a particular sensor from a packet.'

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
        crc ^= ord(data[i])
        for j in range(8):
            if crc & 1 != 0:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc


def format1(input):
    'unsigned 16-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    value = (byte1 << 8) | byte2
    return value

format1.length = 2


def format2(input):
    'signed 16-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    value = ((byte1 & 0x7F) << 8) | byte2
    return value if byte1 & 0x80 == 0 else -value

format2.length = 2


def format3(input):
    'hex string'
    return str(hex(ord(input)))[2:]  # explain [2:]?

format3.length = 6


def format4(input):
    'unsigned 24-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    byte3 = ord(input[2])
    value = (byte1 << 16) | (byte2 << 8) | (byte3)
    return value

format4.length = 3


def format5(input):
    'signed 24-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    byte3 = ord(input[2])
    value = ((byte1 & 0x7F) << 16) | (byte2 << 8) | (byte3)
    return value if byte1 & 0x80 == 0 else -value

format5.length = 3


def format6(input):
    'floating point 1'
    # F6 - float input, +-{0-127}.{0-99} - 1S|7Bit_Int 0|7Bit_Frac{0-99}
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    # have to be careful here, we do not want three decimal placed here.
    value = (byte1 & 0x7F) + (((byte2 & 0x7F) % 100) * 0.01)
    if (byte1 & 0x80) == 0x80:
        value = value * -1
    return value

format6.length = 2


def format7(input):
    'unsigned 8-bit integer[4]'
    # F7 - byte input[4], {0-0xffffffff} - Byte1 Byte2 Byte3 Byte4
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    byte3 = ord(input[0])
    byte4 = ord(input[1])
    return [byte1, byte2, byte3, byte4]

format7.length = 4


def format8(input):
    'floating point 2'
    # F8 - float input, +-{0-31}.{0-999} - 1S|5Bit_Int|2MSBit_Frac 8LSBits_Frac
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    value = ((byte1 & 0x7c) >> 2) + ((((byte1 & 0x03) << 8) | byte2) * 0.001)
    if byte1 & 0x80 != 0:
        value = value * -1
    return value

format8.length = 2


def string3(input):
    'string of format3'
    return ''.join([str(format3(byte)) for byte in input])

string3.length = -1


def string6(input):
    'string of format6'
    return ''.join([str(format6(byte)) for byte in input])

string6.length = -1


def sensor17(input):
    'temperature array sensor'
    return string6(input[::2])

sensor17.length = -1


sensor_table = {
    0x00: ('Board MAC', [('MAC Address', string3)]),
    0x01: ('TMP112', [('Temperature', format6)]),
    0x02: ('HTU21D', [('Temperature', format6),
                      ('Humidity', format6)]),
    0x03: ('GP2Y1010AU0F', [('Dust', format5)]),
    0x04: ('BMP180', [('Temperature', format6),
                      ('Atm Pressure', format5)]),
    0x05: ('PR103J2', [('Temperature', format1)]),
    0x06: ('TSL250RD', [('Light', format1)]),
    0x07: ('MMA8452Q', [('Accel X', format6),
                        ('Accel Y', format6),
                        ('Accel Z', format6),
                        ('RMS', format6)]),
    0x08: ('SPV1840LR5H-B', [('Sound Pressure', format1)]),
    0x09: ('TSYS01', [('Temperature', format6)]),
    0x0A: ('HMC5883L', [('B Field X', format8),
                        ('B Field Y', format8),
                        ('B Field Z', format8)]),
    0x0B: ('HIH6130', [('Temperature', format6),
                       ('Humidity', format6)]),
    0x0C: ('APDS-9006-020', [('Light', format1)]),
    0x0D: ('TSL260RD', [('Light', format1)]),
    0x0E: ('TSL250RD', [('Light', format1)]),
    0x0F: ('MLX75305', [('Light', format1)]),
    0x10: ('ML8511', [('Light', format1)]),
    0x11: ('D6T', [('Temperatures', sensor17)]),
    0x12: ('MLX90614', [('Temperature', format6)]),
    0x13: ('TMP421', [('Temperature', format6)]),
    0x14: ('SPV1840LR5H-B', [('Sound Pressure', format1)]),
    0x15: ('Total reducing gases', [('Concentration', format5)]),
    0x16: ('Ethanol (C2H5-OH)', [('Concentration', format5)]),
    0x17: ('Nitrogen Di-oxide (NO2)', [('Concentration', format5)]),
    0x18: ('Ozone (03)', [('Concentration', format5)]),
    0x19: ('Hydrogen Sulphide (H2S)', [('Concentration', format5)]),
    0x1A: ('Total Oxidizing gases', [('Concentration', format5)]),
    0x1B: ('Carbon Monoxide (C0)', [('Concentration', format5)]),
    0x1C: ('Sulfur Dioxide (SO2)', [('Concentration', format5)]),
    0x1D: ('SHT25', [('Temperature', format2),
                     ('Humidity', format2)]),
    0x1E: ('LPS25H', [('???', format2),
                      ('???', format4)]),
    0x1F: ('Si1145', [('???', format1)]),
    0x20: ('Intel MAC', [('MAC Address', string3)]),
    0xFE: ('Sensor Health', [('Status', format7)]),
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
        if fmt.length < 0:
            yield name, fmt, start, None
            break
        else:
            yield name, fmt, start, start + fmt.length
            start += fmt.length


def unpack_sensor_data(sensor_format, sensor_data):
    return [fmt(sensor_data[start:end])
            for name, fmt, start, end in sensor_format_slices(sensor_format)]


def parse_sensor(identifier, sensor_data):
    if identifier not in sensor_table:
        raise UnknownSensorError(sensor_id=identifier)

    entry_sensor, sensor_format = sensor_table[identifier]
    entry_values = unpack_sensor_data(sensor_format, sensor_data)
    entry_names = [name for name, _ in sensor_format]

    return MessageEntry(entry_sensor, list(zip(entry_names, entry_values)))
