#!/usr/bin/env python3

#Program to detect appearance of preset colors in an image
import cv2
import numpy as np
import sys
import math

def distance3D(x,y):	
    return ((1.0*x[0]-y[0])**2+(1.0*x[1]-y[1])**2+(1.0*x[2]-y[2])**2)**(0.5)

def distance2D(x,y):
    return ((1.0*x[0]-y[0])**2+(1.0*x[1]-y[1])**2)**(0.5)

def averageColor(image,x,y,r):
    total=[0,0,0]
    count=0
    for dx in [-1*r, r]:
        for dy in [-1*r, r]:
	    if x+dx <0: continue
	    if x+dx >= image.shape[0]: continue
	    if y+dy <0: continue
	    if y+dy >= image.shape[1]: continue
	    total[0] = total[0]+image[x+dx][y+dy][0]
	    total[1] = total[1]+image[x+dx][y+dy][1]
	    total[2] = total[2]+image[x+dx][y+dy][2]
	    count=count+1
    total[0]=total[0]/count
    total[1]=total[1]/count
    total[2]=total[2]/count
    return total

def nearestNeighbor(colors, pixel):
    dist = -1
    index=-1
    i=0
    for c in colors:
        d=distance3D(pixel, c)
	if dist==-1 or d<dist:
            dist = d
	    index = i 
	i=i+1
    return index

#cap = cv2.VideoCapture(0)#for built in webcam
#cap = cv2.VideoCapture(1)#for external USB webcam

COUNTER=50
#COUNTER=27
quit=False
while not quit:
    #retval,image = cap.read()
    key = cv2.waitKey()
    while True:
        vertexNames = None
	graph = None

	#retval,image = cap.read()
	image = cv2.imread('pictures/circles.png')
	image = cv2.medianBlur(image,3)
	cimg = image.copy()
	img = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	circles = cv2.HoughCircles(img,cv2.cv.CV_HOUGH_GRADIENT,1,30,
                       			    param1=45,param2=25,minRadius=0,maxRadius=50)
	if circles!=None:
	    circles = np.uint16(np.around(circles))
	    colorNames = ['Red', 'Orange', 'Blue','Green','Yellow','Black']
	    color = [[0,0,255], [51,153,255], [200,100,0], [100,255,100], [76,230,213],[0,0,0]]
	    count = [0,0,0,0,0,0]
	    for i in circles[0,:]:
	        circleColor = averageColor(image, i[1], i[0], 1)
		color_index = nearestNeighbor(color, circleColor)
		count[color_index]=count[color_index]+1

		# draw the outer circle
		cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
		cv2.putText(cimg, colorNames[color_index], (i[0],i[1]), cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,0),2)			
	cv2.imshow('Original', image)
	cv2.imshow('Colors', cimg)
	#cv2.imwrite('Colored.jpg',cimg)
	key = cv2.waitKey(50)
	if key==-1: continue
	if chr(key % 256)=='q': 
            quit=True
	    break

#cap.release()
cv2.destroyAllWindows()
