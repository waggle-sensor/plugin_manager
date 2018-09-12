#!/usr/bin/env python3

import cv2
import numpy as np
import os
import time
import datetime
import argparse
import logging
import pika
import json
import threading

import sys
sys.path.append('/usr/lib/waggle/edge_processor/image')
from processor import *

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

datetime_format = '%a %b %d %H:%M:%S %Z %Y'

# Run modes
# batch: Accumulating detection counts during the time period of a day
MODE_BATCH = 'batch'
# stream: Sending

# burst: Sending an image with detection information when detection occurs
MODE_BURST = 'burst'

def default_configuration():
    conf = {
        'classifier': '/etc/waggle/pedestrian_classifier.xml',
        'start_time': time.strftime(datetime_format, time.gmtime()),
        'end_time': time.strftime(datetime_format, time.gmtime()),
        'daytime': ('00:00:00', '23:59:59'),
        'target': 'bottom',
        'interval': 1,
        'mode': MODE_BURST,
        'verbose': False
    }
    return conf


class Classifier(object):
    def __init__(self):
        self.hog = None
        pass

    def load_classifier(self, classifier_path, window_size=(64, 128)):
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        n_bins = 9
        derive_aperture = 1
        win_sigma = 4.
        histogram_norm_type = 0
        l2_hys_threshold = 2.0e-01
        gamma_correction = 0
        n_levels = 64

        self.hog = cv2.HOGDescriptor(window_size, block_size, block_stride, cell_size,
            n_bins, derive_aperture, win_sigma, histogram_norm_type, l2_hys_threshold,
            gamma_correction, n_levels)

        svm_model = cv2.ml.SVM_load(classifier_path)
        rho = np.ones((1, 1), dtype=np.float32)
        rho_value, alpha, svdix = svm_model.getDecisionFunction(0)
        rho[0] = -1 * rho_value
        vector = svm_model.getSupportVectors().transpose()
        vector_rho = np.concatenate((vector, rho))

        self.hog.setSVMDetector(vector_rho)
        return True

    def classify(self, image, win_stride=(8, 8), padding=(32, 32), scale=1.05, final_threshold=2):
        founds, weights = self.hog.detectMultiScale(image, winStride=win_stride, padding=padding, scale=scale, finalThreshold=final_threshold)

        return founds, weights


class PedestrianDetectionProcessor(Processor):
    def __init__(self, classifier_path):
        super().__init__()
        self.options = default_configuration()
        self.detector = Classifier()
        self.detector.load_classifier(classifier_path)

    def setValues(self, options):
        self.options.update(options)

    def close(self):
        for in_handler in self.input_handler:
            in_handler.close()
        for out_handler in self.output_handler:
            out_handler.close()

    def read(self):
        for stream in self.input_handler:
            if stream is None:
                return False, None
            return stream.read()

    def write(self, packet):
        for stream in self.output_handler:
            if stream is None:
                return False
            stream.write(packet.output())
            if self.options['verbose']:
                logger.info('A packet is sent to output')

    def detect(self, image):
        return self.detector.classify(image)

    def batch_mode_callback(self, packet):
        nparray_raw = np.fromstring(packet.raw, np.uint8)
        image = cv2.imdecode(nparray_raw, 1)
        founds, weights = self.detect(image)
        # simply adds up the detections
        if len(founds) > 0:
            self.detection_meta = packet.meta_data
            self.detection_total += len(founds)

    def burst_mode_callback(self, packet):
        nparray_raw = np.fromstring(packet.raw, np.uint8)
        image = cv2.imdecode(nparray_raw, 1)
        founds, weights = self.detect(image)

        if len(founds) > 0:
            packet.data.append({'pedestrian_detection': [founds.tolist(), weights.tolist()]})
            self.write(packet)

    def check_daytime(self, current_time, daytime_start, duration):
        time_now = datetime.datetime.fromtimestamp(current_time)
        daytime_start = time_now.replace(hour=daytime_start[0], minute=daytime_start[1], second=daytime_start[2])

        diff_in_second = (time_now - daytime_start).total_seconds()
        if diff_in_second < 0:
            return False, abs(diff_in_second)
        elif diff_in_second > duration:
            return False, 3600 * 24 - diff_in_second # wait until midnight
        return True, 0

    def run(self):
        logger.info('Detector initiated')
        logger.info('Wait until start time comes')
        while time.time() <= self.options['start_time']:
            time.sleep(self.options['start_time'] - time.time())

        process_callback = None
        if self.options['mode'] == MODE_BATCH:
            process_callback = self.batch_mode_callback
            self.detection_total = 0
        elif self.options['mode'] == MODE_BURST:
            process_callback = self.burst_mode_callback

        daytime_duration = 3600 * 24 # covers one full day; collect all day long
        daytime_start = [0, 0, 0] # Default
        try:
            daytime_start = [int(x) for x in self.options['daytime'][0].split(':')]
            daytime_end = [int(x) for x in self.options['daytime'][1].split(':')]
            daytime_duration = (daytime_end[0] - daytime_start[0]) * 3600 + (daytime_end[1] - daytime_start[1]) * 60 + (daytime_end[2] - daytime_start[2])
        except Exception as ex:
            logger.error(str(ex))

        logger.info('Detector with %s mode begins...' % (self.options['mode'],))
        packet = None
        try:
            last_updated_time = time.time()
            while True:
                current_time = time.time()
                if current_time - last_updated_time > self.options['interval']:
                    result, wait_time = self.check_daytime(current_time, daytime_start, daytime_duration)
                    if result:
                        f, packet = self.read()
                        if f:
                            process_callback(packet)
                        else:
                            time.sleep(self.options['interval'])
                    else:
                        time.sleep(wait_time)
                else:
                    time.sleep(self.options['interval'] - int(current_time - last_updated_time))

                if current_time > self.options['end_time']:
                    logger.info('Detection is done')
                    # For batch mode, send the result when terminated
                    if self.options['mode'] == MODE_BATCH:
                        packet = Packet()
                        packet.meta_data = self.detection_meta
                        packet.data.append({'pedestrian_detection_batch': [self.detection_total]})
                        self.write(packet)
                    break
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            logger.error(str(ex))


def save_outputs(image, detections, output_path, extension='.jpg', image_size=(64, 128)):
    last_file_name_count = len(os.listdir(output_path))
    for x, y, w, h in detections:
        cropped_image = image[y:y+h, x:x+w]
        resized_image = cv2.resize(cropped_image, image_size, interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(output_path, str(last_file_name_count).zfill(5) + extension), resized_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        last_file_name_count += 1


EXCHANGE = 'image_pipeline'
ROUTING_KEY_RAW = '0'
ROUTING_KEY_EXPORT = '9'

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', dest='config_file', help='Specify config file')
    args = parser.parse_args()

    config_file = None
    if args.config_file:
        config_file = args.config_file
    else:
        config_file = '/etc/waggle/image_pedestrian_detection.conf'

    config = None
    if os.path.isfile(config_file):
        try:
            with open(config_file) as file:
                config = json.loads(file.read())
        except Exception as ex:
            logger.error('Cannot load configuration: %s' % (str(ex),))
            exit(-1)
    else:
        config = default_configuration()
        with open(config_file, 'w') as file:
            file.write(json.dumps(config))
        logger.info('No config specified; default will be used. For detail, check /etc/waggle/image_pedestrian_detection.conf')

    if not os.path.exists(config['classifier']):
        logger.error('Classifier must be presented')
        exit(-1)

    if config['start_time'] is None or config['end_time'] is None:
        logger.error('start and end date must be provided')
        exit(-1)

    try:
        config['start_time'] = time.mktime(time.strptime(config['start_time'], datetime_format))
        config['end_time'] = time.mktime(time.strptime(config['end_time'], datetime_format))
    except Exception as ex:
        logger.error(str(ex))
        exit(-1)

    logger.info('Loading the classifier: ' + config['classifier'])
    processor = PedestrianDetectionProcessor(config['classifier'])
    stream = RabbitMQStreamer(logger)
    stream.config(EXCHANGE, ROUTING_KEY_RAW, ROUTING_KEY_EXPORT)
    result, message = stream.connect()
    if result:
        processor.add_handler(stream, 'in-out')
    else:
        logger.error('Cannot run RabbitMQ %s ' % (message,))
        exit(-1)
    processor.setValues(config)
    processor.run()

    processor.close()
    logger.info('Pedestrian detector terminated')


if __name__ == '__main__':
    main()
