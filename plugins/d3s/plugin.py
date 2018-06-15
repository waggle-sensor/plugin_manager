#!/usr/bin/env python3
import time
import os
import time
import os
import struct
from serial import Serial
from waggle.pipeline import Plugin
from waggle.protocol.v5.encoder import encode_frame


def flush_device(ser):
    while True:
        data = ser.read(1)
        if not data:
            break


set_gain = 0x02
get_gain = 0x82

set_bias = 0x07
get_bias = 0x87

get_serial_no = 0x88
set_hard_lld_channel_report = 0x09
get_hard_lld_channel_report = 0x89
get_fw_ver = 0x8a
set_soft_lld_enable = 0x0c
get_soft_lld_enable = 0x8c

get_soft_lld_channel_report = 0x92
set_soft_lld_channel_report = 0x12

radiometrics = 0xc2
spectrum_report = 0xc1
extended_spectrum = 0xce

d3s_sensor_id = 0xa3

# H length
# B mode
# rest content
header_struct = struct.Struct('<HB')

content_fields = [
    ('compID', 'B'),
    ('reportID', 'B'),

    ('status', 'I'),

    ('realTimeMs', 'I'),
    ('realTimeOffsetMs', 'I'),

    ('dose', 'f'),
    ('doseRate', 'f'),
    ('doseUserAccum', 'f'),

    ('neutronLiveTime', 'I'),
    ('neutronCount', 'I'),
    ('neutronTemperature', 'h'),
    ('neutronResv', 'f'),

    ('gammaLiveTime', 'I'),
    ('gammaCount', 'I'),
    ('gammaTemperature', 'h'),
    ('gammaResv', 'f'),

    ('spectrumBitSize', 'B'),
    ('spectrumResv', 'B'),
]

content_names = [name for name, _ in content_fields]
content_struct = struct.Struct('<' + ''.join(type for _, type in content_fields))


class CoresensePlugin4(Plugin):

    plugin_name = 'd3s'
    plugin_version = '0'

    def run(self):
        device = os.environ.get('D3S_DEVICE', '/dev/waggle_d3s')

        with Serial(device, baudrate=9600, timeout=3) as file:
            while True:
                flush_device(file)
                time.sleep(1)

                # write command
                data_out = bytes([7, 0, 0, 7, radiometrics, 0, 0])
                file.write(data_out)
                time.sleep(1)

                header_data = file.read(header_struct.size)
                content_data = file.read(content_struct.size)

                header = header_struct.unpack(header_data)
                content = content_struct.unpack(content_data)

                print('header:')
                print('length', header[0])
                print('mode', header[1])
                print()

                print('content:')

                for name, value in zip(content_names, content):
                    print(name, value)

                print()

                print('raw:', content_data)
                print('len:', len(content_data))
                print()

                message = encode_frame({d3s_sensor_id: [content_data]})
                self.send(sensor='content', data=message)


if __name__ == '__main__':
    plugin = CoresensePlugin4.defaultConfig()
    plugin.run()
