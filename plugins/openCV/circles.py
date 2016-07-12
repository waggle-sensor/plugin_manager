#!/usr/bin/env python3

#Program to detect preset shapes in an image
import cv2
import numpy as np

img = cv2.imread('pictures/shapes.jpg')
img = cv2.medianBlur(img,3)
original = img.copy()
cimg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

circles = cv2.HoughCircles(cimg,cv2.cv.CV_HOUGH_GRADIENT,1,30,param1=45,param2=25,minRadius=0,maxRadius=50)

circles = np.uint16(np.around(circles))
for i in circles[0,:]:
    # draw the outer circle
    cv2.circle(img,(i[0],i[1]),i[2],(0,255,0),2)
    # draw the center of the circle
    cv2.circle(img,(i[0],i[1]),2,(0,0,0),3)

while(True):
    key = cv2.waitKey(50)
    cv2.imshow('Original', original)
    cv2.imshow('Circles',  img)
    #cv2.imwrite('Detected.jpg',img)
    if key == -1: continue
    if chr(key % 256)=='q': 
        break
cv2.destroyAllWindows()
