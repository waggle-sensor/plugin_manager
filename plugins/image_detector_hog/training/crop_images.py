#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

import argparse
import sys
import cv2
import os


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

dragging = False
scaling = False
refPt = (0, 0)
refPt2 = (0, 0)
prev = (-1, -1)
target_resolution = (64, 128)

def main():
    global refPt, refPt2, target_resolution
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', dest='image_path', help='Path to the images')
    parser.add_argument('--out', dest='output_path', help='Path to store cropped images')
    parser.add_argument('--screen-width', dest='screen_width', help='Set screen width')
    parser.add_argument('--screen-height', dest='screen_height', help='Set screen height')
    args = parser.parse_args()

    extension = '.jpg'
    screen_width = screen_height = sys.maxsize

    if not args.image_path or not args.output_path:
        parser.print_help()
        exit(-1)
    if not args.screen_width and not args.screen_height:
        parser.print_help()
        exit(-1)

    input_dir = os.path.expanduser(args.image_path)
    output_dir = os.path.expanduser(args.output_path)
    if args.screen_width:
        screen_width = int(args.screen_width)
    if args.screen_height:
        screen_height = int(args.screen_height)

    list_images = os.listdir(input_dir)
    window_name = 'c to crop, q to next, z to exit'

    def drag_drop_crop(event, x, y, flags, param):
        global refPt, refPt2, dragging, scaling, prev, target_resolution
        if event == cv2.EVENT_RBUTTONDOWN:
            scaling = True
            prev = (x, y)
        elif event == cv2.EVENT_RBUTTONUP:
            scaling = False
        elif event == cv2.EVENT_LBUTTONDOWN:
            dragging = True
            prev = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            dragging = False
        elif event == cv2.EVENT_MOUSEMOVE:
            if dragging:
                dx = x - prev[0]
                dy = y - prev[1]
                prev = (x, y)
                refPt = (refPt[0] + dx, refPt[1] + dy)
                refPt2 = (refPt2[0] + dx, refPt2[1] + dy)
            elif scaling:
                dx = x - prev[0]
                prev = (x, y)
                new_x = refPt2[0] + dx
                new_y = int((new_x - refPt[0]) * (target_resolution[1] / target_resolution[0])) + refPt[1]
                refPt2 = (new_x, new_y)
            else:
                return
        image = clone.copy()
        cv2.rectangle(image, refPt, refPt2, (0, 255, 0), 3)
        cv2.imshow(window_name, image)

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, drag_drop_crop)

    count = len(os.listdir(output_dir))
    total_length = len(list_images)
    for index, image_file in enumerate(list_images):
        try:
            image_raw = cv2.imread(os.path.join(input_dir, image_file))
            if screen_width < screen_height:
                image = resize(image_raw, width=(min(screen_width, image_raw.shape[0])))
            else:
                image = resize(image_raw, height=(min(screen_height, image_raw.shape[1])))
            txt = '({}/{})'.format(str(index), str(total_length))
            cv2.putText(image, txt, (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            clone = image.copy()

            refPt = (0, 0)
            refPt2 = target_resolution
            stop = False
            while True:
                cv2.imshow(window_name, image)
                key = cv2.waitKey() & 0xff

                if key == ord('q'):
                    break
                elif key == ord('c'):
                    if len(refPt) == 2:
                        roi = clone[refPt[1]:refPt2[1], refPt[0]:refPt2[0]]
                        roi_resized = cv2.resize(roi, target_resolution, interpolation=cv2.INTER_AREA)
                        #cv2.imshow('result', roi_resized)
                        ret = cv2.imwrite(os.path.join(output_dir, str(count).zfill(5) + extension), roi_resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
                        # print(ret)
                        count += 1
                elif key == ord('z'):
                    stop = True
                    break
            if stop:
                break
        except Exception as ex:
            print(ex)

if __name__ == '__main__':

    main(
