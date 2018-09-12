"""
Mask R-CNN
Train on the COCO dataset and implement bounding boxex, label, and mask polygons.

Copyright (c) 2018 Matterport, Inc.
Licensed under the MIT License (see LICENSE for details)
Written by Waleed Abdulla
Modified by Seongha Park
------------------------------------------------------------
    # Apply to an image
    python3 demo.py --image=<URL or path to file>
"""
import cv2
# Use device on /dev/video1
cam = cv2.VideoCapture(1)
cv2.namedWindow("test")

import time

import os
import sys
import json
import datetime
import numpy as np

# Root directory of the project
ROOT_DIR = os.getcwd()
IMAGE_DIR =  os.path.join(ROOT_DIR, "images")

# Dictionary for detection results
detected_objects = {}

# Import Mask RCNN
sys.path.append(ROOT_DIR)
import utils
import model as modellib

import coco
import skimage.io

from skimage.measure import find_contours
import random
import colorsys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon

# Directory to save logs and trained model
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

# Path to trained weights file
COCO_WEIGHTS_PATH = os.path.join(ROOT_DIR, "mask_rcnn_coco.h5")

# Directory to save logs and model checkpoints, if not provided
# through the command line argument --logs
DEFAULT_LOGS_DIR = os.path.join(ROOT_DIR, "logs")

############################################################
#  Configurations
############################################################

# COCO Class names
# Index of the class in the list is its ID. For example, to get ID of
# the teddy bear class, use: class_names.index('teddy bear')
class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
               'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
               'cat', 'dog',
               'horse', 'sheep', 'cow', 'elephant', 'bear',
               'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
               'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
               'kite', 'baseball bat', 'baseball glove', 'skateboard',
               'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
               'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
               'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
               'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
               'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
               'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
               'teddy bear', 'hair drier', 'toothbrush']

class InferenceConfig(coco.CocoConfig):
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1

def display_instances(image, boxes, masks, class_ids, class_names,
                      scores=None, title="",
                      figsize=(16, 16), ax=None):
    """
    boxes: [num_instance, (y1, x1, y2, x2, class_id)] in image coordinates.
    masks: [height, width, num_instances]
    class_ids: [num_instances]
    class_names: list of class names of the dataset
    scores: (optional) confidence scores for each box
    figsize: (optional) the size of the image.
    """
    # display_start = time.time()

    # Number of instances
    N = boxes.shape[0]
    if not N:
        print("\n*** No instances to display *** \n")
    else:
        assert boxes.shape[0] == masks.shape[-1] == class_ids.shape[0]

    if not ax:
        _, ax = plt.subplots(1, figsize=figsize)

    # Generate random colors
    colors = random_colors(N)

    # Copy image before mask objects
    masked_image = image.astype(np.uint32).copy()

    for i in range(N):
        color = colors[i]

        # Bounding box --> took 0.00 seconds for each box, but total display time took 0.89 seconds with only bounding boxes
        if not np.any(boxes[i]):
            # Skip this instance. Has no bbox. Likely lost in image cropping.
            continue
        y1, x1, y2, x2 = boxes[i]
        p = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2,
                              alpha=0.7, linestyle="dashed",
                              edgecolor=color, facecolor='none')
        ax.add_patch(p)

        # Label --> took 0.00 seconds for each label, but total display time took 0.96 seconds with bounding boxes and labels
        class_id = class_ids[i]
        score = scores[i] if scores is not None else None
        label = str(i) + ": " + class_names[class_id]
        x = random.randint(x1, (x1 + x2) // 2)
        caption = "{} {:.3f}".format(label, score) if score else label
        ax.text(x1, y1 + 8, caption,
                color='w', size=11, backgroundcolor="none")

        # Mask Polygon --> took 0.03 - 0.05 seconds for each mask polygon,
        # but total display time took 2.30 seconds with bounding boxes, labels and mask polygons
        # Pad to ensure proper polygons for masks that touch image edges.
        mask = masks[:, :, i]
        padded_mask = np.zeros(
            (mask.shape[0] + 2, mask.shape[1] + 2), dtype=np.uint8)
        padded_mask[1:-1, 1:-1] = mask
        contours = find_contours(padded_mask, 0.7)
        for verts in contours:
            # Subtract the padding and flip (y, x) to (x, y)
            verts = np.fliplr(verts) - 1
            p = Polygon(verts, facecolor="none", edgecolor=color)
            ax.add_patch(p)

    ax.imshow(masked_image.astype(np.uint8))
    # plt.savefig('splash_vis_{:%Y%m%dT%H%M%S}.png'.format(datetime.datetime.now()))
    plt.savefig('splash.png')

    # display_end = time.time()
    # print("Display Elapsed %.2f" % (display_end - display_end))


def random_colors(N, bright=True):
    """
    Generate random colors.
    To get visually distinct colors, generate them in HSV space then
    convert to RGB.
    """
    brightness = 1.0 if bright else 0.7
    hsv = [(i / N, 1, brightness) for i in range(N)]
    colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
    random.shuffle(colors)
    return colors

def detect_and_color_splash(model, image_path=None):
    assert image_path or video_path

    # Run model detection and generate the color splash effect
    # Read image --> takes ~ 0.02 second for splash
    image = skimage.io.imread(args.image)
    # # Detect objects
    # detect_start = time.time()
    r = model.detect([image], verbose=0)[0]
    # detect_end = time.time()
    # print("Detect Elapsed %.2f" % (detect_end - detect_start))
    # # Display objects
    display_instances(image, r['rois'], r['masks'], r['class_ids'],
                            class_names, r['scores'])
    for i in range(len(r['rois'])):
        detected_objects[i] = (class_names[r['class_ids'][i]], r['scores'][i])
        # print(class_names[r['class_ids'][i]], r['scores'][i])

def capture_frame():
    # frame_start = time.time()
    for i in range(5):
        ret, frame = cam.read()
        if not ret:
            print('No camera on /dev/video1')
            exit(0)

        cv2.imshow("test", frame)

    img_name = "opencv_frame.png"
    cv2.imwrite(img_name, frame)
    # print('\n', "{} written!".format(img_name))
    # frame_end = time.time()
    # print("Frame Capturing Elapsed %.2f" % (frame_end - frame_start))


def evaluate():
    try:
        if main_image == None:
            capture_frame()
            args.image = "opencv_frame.png"
        detect_and_color_splash(model, image_path=args.image)

    except Exception as ex:
        pass

############################################################
#  Evaluation
############################################################

if __name__ == '__main__':
    import argparse

    main_start = time.time()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Mask R-CNN to detect objects.')
    parser.add_argument('--logs', required=False,
                        default=DEFAULT_LOGS_DIR,
                        metavar="/path/to/logs/",
                        help='Logs and checkpoints directory (default=logs/)')
    parser.add_argument('--image', required=False,
                        metavar="path or URL to image",
                        help='Image to apply the color splash effect on')
    args = parser.parse_args()

    if args.image == None:
        main_image = None

    config = InferenceConfig()

    # Create model --> takes > 2 second for splash
    model = modellib.MaskRCNN(mode="inference", config=config, model_dir=args.logs)

    # Select weights file to load --> takes 0.00 second for splash
    weights_path = COCO_WEIGHTS_PATH
    # Load weights --> takes > 2 second for splash
    # Exclude the last layers because they require a matching
    # number of classes
    model.load_weights(weights_path, by_name=True)

    # Evaluate --> takes > 12 second for splash
    try:
        while True:
            evaluate()

            print('')
            print(detected_objects)
            main_end = time.time()
            print("Evaluation Elapsed %.2f" % (main_end - main_start))
            main_start = time.time()

    except KeyboardInterrupt:
        cam.release()
        cv2.destroyAllWindows()
