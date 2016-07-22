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
import datetime


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

        timestamp = datetime.datetime.utcnow()

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
        """Receives raw packet data from the device."""
        failures = 0

        while True:
            # get more data from device
            self.data.extend(self.serial.read(256))

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
        crc ^= ord(data[i])
        for j in range(8):
            if crc & 1 != 0:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc


def uint16(input):
    'unsigned 16-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    value = (byte1 << 8) | byte2
    return value

uint16.length = 2


def int16(input):
    'signed 16-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    value = ((byte1 & 0x7F) << 8) | byte2
    return value if byte1 & 0x80 == 0 else -value

int16.length = 2


def uint24(input):
    'unsigned 24-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    byte3 = ord(input[2])
    value = (byte1 << 16) | (byte2 << 8) | (byte3)
    return value

uint24.length = 3


def int24(input):
    'signed 24-bit integer'
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    byte3 = ord(input[2])
    value = ((byte1 & 0x7F) << 16) | (byte2 << 8) | (byte3)
    return value if byte1 & 0x80 == 0 else -value

int24.length = 3


def ufloat(input):
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    # have to be careful here, we do not want three decimal placed here.
    value = (byte1 & 0x7F) + (((byte2 & 0x7F) % 100) * 0.01)
    if (byte1 & 0x80) == 0x80:
        value = value * -1
    return value

ufloat.length = 2


def lfloat(input):
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    value = ((byte1 & 0x7c) >> 2) + ((((byte1 & 0x03) << 8) | byte2) * 0.001)
    if byte1 & 0x80 != 0:
        value = value * -1
    return value

lfloat.length = 2


def macaddr(input):
    return ''.join(map(lambda b: '{:02X}'.format(ord(b)), input))
    # return ''.join([str(format3(byte)) for byte in input])

macaddr.length = 6


def uint8array(input):
    'unsigned 8-bit integer[4]'
    # F7 - byte input[4], {0-0xffffffff} - Byte1 Byte2 Byte3 Byte4
    byte1 = ord(input[0])
    byte2 = ord(input[1])
    byte3 = ord(input[2])
    byte4 = ord(input[3])
    return [byte1, byte2, byte3, byte4]

uint8array.length = 4


# def sensor17(input):
#     return string6(input[::2])
#
# sensor17.length = -1


sensor_table = {
    0x00: ('Board MAC', [('MAC Address', macaddr)]),
    0x01: ('TMP112', [('Temperature', ufloat)]),
    0x02: ('HTU21D', [('Temperature', ufloat),
                      ('Humidity', ufloat)]),
    #0x03: ('GP2Y1010AU0F', [('Dust', int24)]),
    0x03: ('HIH4030', [('Humidity', uint16)]),
    0x04: ('BMP180', [('Temperature', ufloat),
                      ('Atm Pressure', int24)]),
    0x05: ('PR103J2', [('Temperature', uint16)]),
    0x06: ('TSL250RD', [('Light', uint16)]),
    0x07: ('MMA8452Q', [('Accel X', ufloat),
                        ('Accel Y', ufloat),
                        ('Accel Z', ufloat),
                        ('RMS', ufloat)]),
    0x08: ('SPV1840LR5H-B', [('Sound Pressure', uint16)]),
    0x09: ('TSYS01', [('Temperature', ufloat)]),
    0x0A: ('HMC5883L', [('B Field X', lfloat),
                        ('B Field Y', lfloat),
                        ('B Field Z', lfloat)]),
    0x0B: ('HIH6130', [('Temperature', ufloat),
                       ('Humidity', ufloat)]),
    0x0C: ('APDS-9006-020', [('Light', uint16)]),
    0x0D: ('TSL260RD', [('Light', uint16)]),
    0x0E: ('TSL250RD', [('Light', uint16)]),
    0x0F: ('MLX75305', [('Light', uint16)]),
    0x10: ('ML8511', [('Light', uint16)]),
    # 0x11: ('D6T', [('Temperatures', sensor17)]),
    0x12: ('MLX90614', [('Temperature', ufloat)]),
    0x13: ('TMP421', [('Temperature', ufloat)]),
    0x14: ('SPV1840LR5H-B', [('Sound Pressure', uint16)]),
    0x15: ('Total reducing gases', [('Concentration', int24)]),
    0x16: ('Ethanol (C2H5-OH)', [('Concentration', int24)]),
    0x17: ('Nitrogen Di-oxide (NO2)', [('Concentration', int24)]),
    0x18: ('Ozone (03)', [('Concentration', int24)]),
    0x19: ('Hydrogen Sulphide (H2S)', [('Concentration', int24)]),
    0x1A: ('Total Oxidizing gases', [('Concentration', int24)]),
    0x1B: ('Carbon Monoxide (C0)', [('Concentration', int24)]),
    0x1C: ('Sulfur Dioxide (SO2)', [('Concentration', int24)]),
    0x1D: ('SHT25', [('Temperature', int16),
                     ('Humidity', uint16)]),
    0x1E: ('LPS25H', [('Temperature', int16),
                      ('Pressure', uint24)]),
    0x1F: ('Si1145', [('Raw UV', uint16),
                      ('Raw VL', uint16),
                      ('Raw IR', uint16)]),
    0x20: ('Intel MAC', [('MAC Address', macaddr)]),
    0x21:('CO ADC Temp', [('ADC Temperature', int16)]),
    0x22:('IAQ/IRR Temp', [('ADC Temperature', int16)]),
    0x23:('O3/NO2 Temp', [('ADC Temperature', int16)]),
    0x24:('SO2/H2S Temp', [('ADC Temperature', int16)]),
    0x25:('CO LMP Temp', [('ADC Temperature', int16)]),
    0x26:('Accelerometer', [('Accel X', int16),
                            ('Accel Y', int16),
                            ('Accel Z', int16),
                            ('Vib Index', uint24)]),
    0x27:('Gyro', [('Orientation X', int16),
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
