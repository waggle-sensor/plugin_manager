#!/usr/bin/python3

import os
import time
import argparse
import json

import cv2
import numpy as np

from waggle.pipeline import Plugin, ImagePipelineHandler
from waggle.protocol.v5.encoder import encode_frame

# Configuration of the pipeline
# name of the pipeline
EXCHANGE = 'image_pipeline'

# output direction of this processor
ROUTING_KEY_EXPORT = 'exporter'  # flush output to Beehive


def get_default_configuration():
    """ ssd_mobilenet_coco default set is in
        https://github.com/opencv/opencv/tree/master/samples/dnn
    """
    conf = {
        'source': 'bottom',
        'model': 'models/ssd_mobilenet_coco.pb',
        'model_desc': 'models/ssd_mobilenet_coco.pbtxt',
        'classes': 'models/ssd_mobilenet_coco.classes',
        'input_scale': 0.00784,
        'input_size': (300, 300),
        'input_mean_subtraction': (127.5, 127.5, 127.5),
        'input_channel_order': 'RGB',
        'detection_interval': 1,  # every 5 mins
        'sampling_interval': -1,  # None, by default
        'detection_confidence': 0.3,  # least detection confidence
    }
    return conf


class CarPedDetector(Plugin):
    plugin_name = 'image_car_ped_detector'
    plugin_version = '0'

    def __init__(self):
        super().__init__()
        self.hrf = False
        self.config = self._get_config_table()
        self.input_handler = ImagePipelineHandler(routing_in=self.config['source'])

    def _get_config_table(self):
        config_file = '/wagglerw/waggle/image_car_ped_detector.conf'
        config_data = None
        try:
            with open(config_file) as config:
                config_data = json.loads(config.read())
        except Exception:
            config_data = get_default_configuration()
            with open(config_file, 'w') as config:
                config.write(json.dumps(config_data, sort_keys=True, indent=4))
        return config_data

    def _detect(self, img_blob, cvNet, classes, confidence=0.3, img_rows=1, img_cols=1):
        cvNet.setInput(img_blob)
        cvOut = cvNet.forward()

        output = {}
        for detection in cvOut[0, 0, :, :]:
            score = float(detection[2])
            if score > confidence:
                class_index = int(detection[1])
                class_name = classes[class_index]
                if class_name not in output:
                    output[class_name] = {}

                detection_index = len(output[class_name].keys())
                left = int(detection[3] * img_cols)
                top = int(detection[4] * img_rows)
                right = int(detection[5] * img_cols)
                bottom = int(detection[6] * img_rows)

                output[class_name][detection_index] = (
                    left, top, right, bottom
                )
        return output

    def _print(self, detected_objects):
        for detected_object in detected_objects:
            print('%s was found at' % (detected_object,))
            for index, rect in detected_objects[detected_object].items():
                left, top, right, bottom = rect
                x = left + ((right - left) / 2.)
                y = top + ((bottom - top) / 2.)
                print('    x:%5d, y:%5d' % (x, y))
            print('Total: %s %d' % (detected_object, len(detected_objects[detected_object].keys())))

    def close(self):
        self.input_handler.close()

    def run(self):
        # Load models
        model_path = self.config['model']
        model_desc = self.config['model_desc']
        if not os.path.exists(model_path):
            print('%s not exist' % (model_path,))
            return

        if not os.path.exists(model_desc):
            print('%s not exist' % (model_desc,))
            return

        _, ext = os.path.splitext(model_path)
        if 'pb' in ext:
            cvNet = cv2.dnn.readNetFromTensorflow(model_path, model_desc)
        elif 'caffemodel' in ext:
            cvNet = cv2.dnn.readNetFromCaffe(model_path, model_desc)
        else:
            print('Model extension not recognized: %s' % (ext,))
            return

        # Load classes
        classes = {}
        with open(self.config['classes'], 'r') as file:
            for line in file:
                sp = line.strip().split(' ')
                classes[int(sp[0])] = sp[1]

        try:
            confidence = float(self.config['detection_confidence'])
        except Exception:
            confidence = 0.3

        self.config['last_updated'] = time.time() - self.config['detection_interval']
        self.config['last_sampled'] = time.time() - self.config['sampling_interval']

        while True:
            current_time = time.time()
            if current_time - self.config['last_updated'] > self.config['detection_interval']:
                return_code, message = self.input_handler.read()
                if return_code is True:
                    print('Received frame')
                    properties, frame = message
                    nparr_img = np.fromstring(frame, np.uint8)
                    img = cv2.imdecode(nparr_img, cv2.IMREAD_COLOR)

                    img_blob = cv2.dnn.blobFromImage(
                        img,
                        self.config['input_scale'],
                        tuple(self.config['input_size']),
                        tuple(self.config['input_mean_subtraction']),
                        swapRB=True if 'RGB' in self.config['input_channel_order'].upper() else False,
                        crop=False
                    )

                    detected_objects = self._detect(
                        img_blob,
                        cvNet,
                        classes,
                        confidence=confidence,
                        img_rows=img.shape[0],
                        img_cols=img.shape[1]
                    )

                    if self.hrf:
                        self._print(detected_objects)
                    else:
                        count_car = 0
                        count_person = 0

                        if 'car' in detected_objects:
                            count_car = len(detected_objects['car'].keys())
                        if 'person' in detected_objects:
                            count_person = len(detected_objects['person'].keys())
                        packet = {
                            0xA1: [count_car, count_person]
                        }
                        waggle_packet = encode_frame(packet)
                        self.send(sensor='', data=waggle_packet)

                        # Sampling the result
                        if current_time - self.config['last_sampled'] > self.config['sampling_interval']:
                            result = {
                                'processing_software': os.path.basename(__file__),
                                'results': json.dumps(detected_objects)
                            }
                            properties.headers.update(result)
                            self.input_handler.write(
                                ROUTING_KEY_EXPORT,
                                frame,
                                properties.headers
                            )
                            self.config['last_sampled'] = current_time
                    self.config['last_updated'] = current_time
            else:
                wait_time = current_time - self.config['last_updated']
                if wait_time > 0.1:
                    time.sleep(wait_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hrf', action='store_true', help='Print in human readable form')
    args = parser.parse_args()

    plugin = CarPedDetector.defaultConfig()
    plugin.hrf = args.hrf
    try:
        plugin.run()
    except (KeyboardInterrupt, Exception) as ex:
        print(str(ex))
    finally:
        plugin.close()
