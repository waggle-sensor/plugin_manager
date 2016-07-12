#!/usr/bin/env python3

#Program to perform background subtraction and motion detection

from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import cv2
import time

def backgroundSubtraction():
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    fgbg = cv2.BackgroundSubtractorMOG()

    while(True):
        # Capture frame-by-frame
        ret, img = cap.read()
        frame = img.copy()

        # Frame operations
        #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fgmask = fgbg.apply(img)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

        # Display the resulting frame
        cv2.imshow("Initial Feed", frame)
        cv2.imshow('Objects',fgmask)
        key = cv2.waitKey(50)
        if key == -1: continue
        if chr(key % 256)=='q': 
            break
    cap.release()

def motionDetection():
    # initialize the first frame in the video stream
    firstFrame = None

    while True:
        ret, frame = cap.read()

        # convert frame to grayscale and blur it
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if firstFrame is None:
            firstFrame = gray
            continue
        # compute the absolute difference between frames
        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
 
        # dilate the thresholded image to fill in holes, then find contours on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        (conts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)

        for c in conts:
        # compute the bounding box for the contour and draw it on the frame
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Initial Feed", frame)
        cv2.imshow("Thresh", thresh)
        #cv2.imshow("Frame Delta", frameDelta)
        key = cv2.waitKey(50)
        if key == -1: continue
        if chr(key % 256)=='q': 
            break
    cap.release()

def hog():
    while(True):
        # initialize the HOG descriptor/person detector
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        ret, img = cap.read()
        orig = img.copy()
        # detect people in the image
        (rects, weights) = hog.detectMultiScale(img, winStride=(4, 4), padding=(8, 8), scale=1.05)
        # draw the original bounding boxes
        for (x, y, w, h) in rects:
            cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # apply non-maxima suppression to the bounding boxes using a fairly large overlap threshold
            rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
            # try to maintain overlapping boxes that are still people
            pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

            # draw the final bounding boxes
            for (xA, yA, xB, yB) in pick:
                cv2.rectangle(img, (xA, yA), (xB, yB), (0, 255, 0), 2)
            # show the output images
        cv2.imshow("Before NMS", orig)
        cv2.imshow("After NMS", img)
        key = cv2.waitKey(50)
        if chr(key % 256)=='q': 
            break
    cap.release()

#Main
if __name__ == '__main__':
    print(" -------------------------------- \n|OpenCV Object Detection/Tracking|\n -------------------------------- \n")
    arg = eval(input("Select detection method:\n[1] Background Subtraction\n[2] Motion detection\n[3] Histogram of Oriented Gradients\n[0] Exit Program\n>"))
    cap = cv2.VideoCapture(1)# uncomment for webcam
    time.sleep(2)
    if cap.isOpened() == False:
        print("Camera not found, trying again")
	cap = cv2.VideoCapture(0)
    #cap = cv2.VideoCapture('videos/ped.mpg') # uncomment for video file
    if arg == 1:
        #startticks = cv2.getCPUTickCount()
        backgroundSubtraction()
        #endticks = cv2.getCPUTickCount()
        #print(endticks - startticks)
    elif arg == 2:
        motionDetection()
    elif arg == 3:
        hog()
    else:
        quit()
    print("Exiting")
    cv2.destroyAllWindows()
