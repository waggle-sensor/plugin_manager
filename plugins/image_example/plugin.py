#!/usr/bin/python3

import time
import binascii
import json

# Import graphics functions
import cv2
import numpy as np

from waggle.pipeline import Plugin, ImagePipelineHandler
from waggle.protocol.v5.encoder import encode_frame_from_flat_string

# Configuration of the pipeline
# name of the pipeline
EXCHANGE = 'image_pipeline'

# output direction of this processor
ROUTING_KEY_EXPORT = 'exporter'  # flush output to Beehive


def get_default_configuration():
    conf = {
        'top': {
            'interval': 300,  # every 5 mins
        },
        'bottom': {
            'interval': 300,  # every 5 mins
        }
    }
    return conf


def load_configuration():
    sensor_config_file = '/wagglerw/waggle/image_example.conf'
    sensor_table = None
    try:
        with open(sensor_config_file) as config:
            sensor_table = json.loads(config.read())
    except Exception:
        sensor_table = get_default_configuration()
        with open(sensor_config_file, 'w') as config:
            config.write(json.dumps(sensor_table, sort_keys=True, indent=4))

    return sensor_table


def get_average_color(image):
    avg_color = np.average(image, axis=0)
    avg_color = np.average(avg_color, axis=0)

    ret = {
        'r': int(avg_color[2]),
        'g': int(avg_color[1]),
        'b': int(avg_color[0]),
    }
    return ret


def get_histogram(image):
    b, g, r = cv2.split(image)

    def get_histogram_in_byte(histogram):
        mmax = np.max(histogram) / 255.  # Normalize it in range of 255
        histogram = histogram / mmax
        output = bytearray()
        for value in histogram:
            output.append(int(value))
        return binascii.hexlify(output).decode()
    r_histo, bins = np.histogram(r, range(0, 256, 15))
    g_histo, bins = np.histogram(g, range(0, 256, 15))
    b_histo, bins = np.histogram(b, range(0, 256, 15))
    ret = {
        'r': get_histogram_in_byte(r_histo),
        'g': get_histogram_in_byte(g_histo),
        'b': get_histogram_in_byte(b_histo),
    }
    return ret


def print_plaintext(report, prefix='', delimiter='_', no_print_for_none=False):
    for key, value in sorted(report.items()):
        if isinstance(value, dict):
            yield from print_plaintext(value, prefix + key + delimiter, no_print_for_none=no_print_for_none)
        else:
            if no_print_for_none:
                if value is not None:
                    yield '{}{} {}'.format(prefix, key, str(value))
            else:
                yield '{}{} {}'.format(prefix, key, str(value))


class ExampleImageProcessor(Plugin):
    plugin_name = 'image_example'
    plugin_version = '0'

    def __init__(self):
        super().__init__()

    """
        Close input/output handlers
        @params: config: Dictionary
    """
    def set_config(self, config):
        self.config = config

    """
        Close input/output handlers
    """
    def close(self):
        # Close Image pipeline handlers
        if self.config is not None:
            for config in self.config:
                if 'handler' in config:
                    config['handler'].close()

    """
        Main function of the processor
        @params: frame: binary blob
                 headers: Dictionary

        @return: (processed frame, processed headers)
    """
    def do_process(self, frame, headers, device_char):
        results = {'device': device_char}

        # Convert frame into JPEG image
        image_format = headers['image_format']
        if 'MJPG' in image_format:
            nparr_img = np.fromstring(frame, np.uint8)
            img = cv2.imdecode(nparr_img, cv2.IMREAD_COLOR)
        else:
            raise Exception('Unknown image format')

        # Obtain basic information of the image
        results['average_color'] = get_average_color(img)
        results['histogram'] = get_histogram(img)

        # Packetizing
        image = {'image': results}
        results_flat_string = print_plaintext(image)
        flat_string_data = '\n'.join(results_flat_string)
        print(flat_string_data)
        encoded_data = encode_frame_from_flat_string(flat_string_data)
        return encoded_data

    """
        Main thread of the processor
    """
    def run(self):
        if self.config is None:
            print('Configuration is not set. Halting...')

        while True:
            current_time = time.time()

            for device, device_config in self.config.items():
                if current_time - device_config['last_updated'] > device_config['interval']:
                    handler = device_config['handler']
                    return_code, message = handler.read()
                    if return_code is True:
                        properties, frame = message
                        print('Received frame')
                        waggle_packet = self.do_process(
                            frame,
                            properties.headers,
                            device_char=device[0])
                        self.send(sensor='frame', data=waggle_packet)
                        device_config['last_updated'] = current_time
                        self.config[device] = device_config
            time.sleep(1)


if __name__ == '__main__':
    try:
        # Spawn the processor with default configuration
        processor = ExampleImageProcessor().defaultConfig()

        # Load configuration
        valid_config = {}
        config = load_configuration()
        for device in config:
            device_config = config[device]

            # Set up a subscriber for the device
            reader = ImagePipelineHandler(routing_in=device)
            device_config['handler'] = reader
            device_config['last_updated'] = 0
            valid_config[device] = device_config

        if valid_config == {}:
            raise Exception('No valid configuration loaded. Exiting...')
        else:
            processor.set_config(valid_config)

        # Processor runs
        processor.run()
    except (KeyboardInterrupt, Exception) as ex:
        print(str(ex))
    finally:
        processor.close()
