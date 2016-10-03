"""
This module provides an interface to the Waggle coresense device.
"""
from serial import Serial, SerialException
from contextlib import contextmanager
import time


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
        frame, data = self.recv_packet_data()
        timestamp = int(time.time())
        return Message(timestamp=timestamp, entries=[], frame=frame)

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

                    frame = bytes(self.data[:HEADER_SIZE + FOOTER_SIZE + length])
                    body = bytes(self.data)[HEADER_SIZE:HEADER_SIZE + length]

                    self.data[0] = 0  # clear frame byte to allow other packets

                    if end == END_BYTE and crc == crc8(body):
                        return frame, body

                    failures += 1

                    if failures >= 10:
                        raise NoPacketError(failures)
            # prevent consuming huge CPU recource
            time.sleep(1)


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

    def __init__(self, timestamp, entries, frame):
        self.timestamp = timestamp
        self.entries = entries
        self.frame = frame

    def __repr__(self):
        return '[{} : {}]'.format(self.timestamp, self.entries)


def crc8(data, crc=0):
    for i in range(len(data)):
        crc ^= data[i]
        for j in range(8):
            if crc & 1 != 0:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc
