#!/usr/bin/env python3

import argparse
import sys
import cv2
import os
import numpy as np

import logging

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# helper classes
class StatModel(object):
    def load(self, fn):
        self.model.load(fn)  # Known bug: https://github.com/opencv/opencv/issues/4969

    def save(self, fn):
        self.model.save(fn)


class SVM(StatModel):
    def __init__(self, C=0.01, gamma=0.5):
        self.model = cv2.ml.SVM_create()
        self.model.setGamma(gamma)
        self.model.setC(C)
        self.model.setKernel(cv2.ml.SVM_LINEAR)
        self.model.setType(cv2.ml.SVM_EPS_SVR)
        self.model.setP(0.1)

    def train(self, samples, responses):
        self.model.train(samples, cv2.ml.ROW_SAMPLE, responses)

    def predict(self, samples):
        return self.model.predict(samples)[1].ravel()


def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]
    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image
    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)
    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))
    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)
    # return the resized image
    return resized


def load_image(path, list_file, target_size=None):
    return_list = []
    try:
        with open(os.path.join(path, list_file)) as file:
            for line in file:
                line = line.strip()
                try:
                    image = cv2.imread(os.path.join(path, line))
                    return_list.append(image.copy())
                except Exception as ex:
                    logger.info('Cannot load %s... %s skip' % (os.path.join(path, line), str(ex)))
    except Exception as ex:
        logger.error('Cannot read %s' % (os.path.join(path, list_file),))
    return return_list


def sample_negative(images, number_of_samples_per_image=10, target_size=(64, 128)):
    return_list = []
    x = np.zeros((1), dtype=np.int32)
    y = np.zeros((1), dtype=np.int32)

    for image in images:
        max_ratio = min(round(image.shape[1] / target_size[0]) - 1, round(image.shape[0] / target_size[1]) - 1)
        scales = range(1, max_ratio)

        for j in scales:
            for i in range(number_of_samples_per_image):
                scaled_win_height = target_size[1] * j
                scaled_win_width = target_size[0] * j

                # generate a random index inside the image
                cv2.randu(x, 0, image.shape[0] - scaled_win_height)
                cv2.randu(y, 0, image.shape[1] - scaled_win_width)
                # get a window of 128x64 image

                neg_image = image[x[0]:x[0] + scaled_win_height, y[0]:y[0] + scaled_win_width, :]
                img_scaled = resize(neg_image, width=target_size[0])
                return_list.append(img_scaled.copy())
    return return_list


def train_hog(images, hog, featureLength, label_value):
    samples = np.zeros((len(images), featureLength), dtype=np.float32)

    for index, image in enumerate(images):
        h = hog.compute(image)
        samples[index, :] = h.reshape(-1, h.shape[0])

    labels = np.zeros((samples.shape[0]), dtype=np.int32)
    labels.fill(label_value)
    return samples, labels


def train(pos_path, pos_list, neg_path, neg_list, output='classifier.xml', binary=None, binary_label=None, verbose=False):
    pre_samples = pre_labels = None
    if binary is not None and binary_label is not None:
        if verbose:
            logger.info('Loading images and labels from %s and %s' % (binary, binary_label))
        with open(binary, 'rb') as file:
            pre_samples = np.load(file)
        
        with open(binary_label, 'rb') as file:
            pre_labels = np.load(file)
            pre_labels.fill(-1)

    win_size = (64, 128)
    blockSize = (16, 16)
    blockStride = (8, 8)
    cellSize = (8, 8)
    nbins = 9
    hog = cv2.HOGDescriptor(win_size, blockSize, blockStride, cellSize, nbins)

    feature_length = int(nbins * (blockSize[0] / cellSize[0]) * (blockSize[1] / cellSize[1]) * (win_size[0] / blockStride[0] - 1) * (win_size[1] / blockStride[1] - 1))

    pos_images = load_image(pos_path, pos_list)
    if verbose:
        logger.info('Load %d positive images' % (len(pos_images),))
    pos_samples, pos_labels = train_hog(pos_images, hog, feature_length, label_value=1)

    neg_images = load_image(neg_path, neg_list)
    cropped_neg_images = sample_negative(neg_images, 100, target_size=win_size)
    if verbose:
        logger.info('Load %d negative images' % (len(cropped_neg_images),))
    neg_samples, neg_labels = train_hog(cropped_neg_images, hog, feature_length, label_value=-1)

    logger.info('Start training classifier...')
    svm = SVM()
    if pre_samples is not None:
        training_samples = np.concatenate((pre_samples, pos_samples, neg_samples))
        training_labels = np.concatenate((pre_labels, pos_labels, neg_labels))
    else:
        training_samples = np.concatenate((pos_samples, neg_samples))
        training_labels = np.concatenate((pos_labels, neg_labels))
    svm.train(training_samples, training_labels)
    logger.info('Done.')
    svm.save(output)
    logger.info('The classifier is ready %s' % (output,))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-pd', dest='positive_image_path', help='Path to positive images')
    parser.add_argument('-p', dest='positive_image_list', help='List of the positive images')
    parser.add_argument('-nd', dest='negative_image_path', help='Path to negative images')
    parser.add_argument('-n', dest='negative_image_list', help='List of the negative images')
    parser.add_argument('-o', dest='output_classifier', help='Output name of classifier')

    parser.add_argument('-b', dest='binary_images', help='Path to binary images')
    parser.add_argument('-bl', dest='binary_images_label', help='Path to label of the binary images')

    parser.add_argument('-hnd', dest='hard_neg_image_path', help='Path to images for hard-negative-mining')
    parser.add_argument('-hn', dest='hard_neg_image_list', help='List of the images for hard-negative-mining')
    parser.add_argument('-hnic', dest='hn_input_classifier', help='Target classifier for hard-negative-mining')
    parser.add_argument('-hnoc', dest='hn_output_classifier', help='Name of hard-nagative-mined classifier')

    parser.add_argument('-v', dest='verbose', help='Show messages', action='store_true')
    args = parser.parse_args()
    verbose = args.verbose

    if args.positive_image_path and args.positive_image_list and args.negative_image_path and args.negative_image_list:
        logger.info('Perform training from positive and negative images')
        train(
            args.positive_image_path,
            args.positive_image_list,
            args.negative_image_path,
            args.negative_image_list,
            output=args.output_classifier,
            binary=args.binary_images,
            binary_label=args.binary_images_label,
            verbose=verbose)

if __name__ == '__main__':
    main()