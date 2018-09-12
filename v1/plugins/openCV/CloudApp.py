# This python program uses openCV and skimage to detect the percentage of cloud coverage in a camera image and uses this data
# to make a prediction of the weather. It also uses Caffe to classify the type of cloud environment that is observed.
#Usage: python CloudApp.py <image>.jpg
from __future__ import division
from skimage.segmentation import mark_boundaries
from skimage.segmentation import slic
from skimage.util import img_as_float
import sys, os
import numpy as np
os.environ['GLOG_minloglevel'] = '2' #This line hides Caffe's lengthy layer output
import caffe
import cv2

def run_caffe():
    print 'Initializing Caffe....\n'
    sys.path.insert(0, '.') #Make sure you are running from /AppFiles directory

    MODEL_FILE = 'AppFiles/deploy.prototxt'
    PRETRAINED = 'AppFiles/caffenet_train_iter_250.caffemodel'
    MEAN_FILE = np.load('AppFiles/mean.npy').mean(1).mean(1)

    caffe.set_mode_cpu()
    net = caffe.Classifier(MODEL_FILE, PRETRAINED,
                       mean=MEAN_FILE,
                       channel_swap=(2,1,0),
                       raw_scale=255,
                       image_dims=(64, 64))
    
    for arg in sys.argv[1:]:
        input_image = caffe.io.load_image(arg)
    
    print 'Classifying ' + arg + '.....\n'

    prediction = net.predict([input_image], oversample=False)
    output = net.forward()
    output_prob = output['prob'][0]  # the output probability vector for the first image in the batch

    # load ImageNet labels
    labels_file = 'AppFiles/synset_words.txt'    
    labels = np.loadtxt(labels_file, str, delimiter='\t')
    # sort top five predictions from softmax output
    top_inds = output_prob.argsort()[::-1][:5]  # reverse sort and take five largest items
    for i in top_inds:
        per = output_prob[i] * 100  
        print "{:10.4f}".format(per), 'percent accuracy for guess', labels[i]

    #viewing model weights
    net = caffe.Net(MODEL_FILE, PRETRAINED, caffe.TEST)
    params = ['conv1', 'conv2', 'fc6']
    # fc_params = {name: (weights, biases)}
    fc_params = {pr: (net.params[pr][0].data, net.params[pr][1].data) for pr in params}

    for fc in params:
        print '\n{} weights are {} dimensional and biases are {} dimensional'.format(fc, fc_params[fc][0].shape, fc_params[fc][1].shape)


def resize(im):
    height, width = 2592, 1944
    res = cv2.resize(im,(0,0), fx=0.5, fy=0.5)#resize photo to 1/4 original size
    return res

def superPixel(image):
    #def colors in HSV
    low_blue = np.array([90,50,50])
    high_blue = np.array([130,255,255])
    # show the output of SLIC
    print '\nPerforming superpixel calculations...\n'
    segments = slic(img_as_float(image), n_segments = 50, sigma = 5)#SLIC superpixel algorithm
    '''Uncomment to see mapping of superpixels for each image 
    fig = plt.figure("Superpixels")
    ax = fig.add_subplot(1, 1, 1)
    ax.imshow(mark_boundaries(img_as_float(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)), segments))
    plt.axis("off")
    plt.show()
    '''
    bigMask = np.zeros(image.shape[:2], dtype = "uint8")
    finalBlue = image.copy()
    # loop over the unique segment values
    for (i, segVal) in enumerate(np.unique(segments)):
        # construct a mask for the segment
        mask = np.zeros(image.shape[:2], dtype = "uint8")
        mask[segments == segVal] = 255
        img = cv2.bitwise_and(image, image, mask = mask) #this is the current superpixel
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  #view superpixel in HSV colors
        blueMask = cv2.inRange(hsv, low_blue, high_blue) #apply a blue mask to each superpixel
        bigMask += blueMask
    newMask = np.zeros(image.shape[:2], dtype = "uint8")
    newMask = cv2.bitwise_not(bigMask, newMask)       #flip the big mask so it finds everything that is not blue
    #calculations on percent cloud cover
    numCloudPix = cv2.countNonZero(newMask)
    numTotalPix = cv2.countNonZero(bigMask) + numCloudPix #5038848?
    percentCloudPix =  ((numCloudPix / numTotalPix) * 100)
    finalBlue = cv2.bitwise_and(finalBlue, finalBlue, mask = newMask)  #apply non-blue mask to original image
    line = ("Cloud coverage: %d%%" % percentCloudPix)
    if percentCloudPix >= 70:
        line = line + " Status: Overcast Clouds"
    elif percentCloudPix < 70 and percentCloudPix >= 25:
        line = line + " Status: Moderate Clouds"
    elif percentCloudPix < 25 and percentCloudPix >= 1 :
        line = line + " Status: Clear Skies"
    elif percentCloudPix < 1:
        line = "Cannot detect clouds: Camera is obstructed or it is night."
    finalBlue = resize(finalBlue)
    #cv2.putText(finalBlue,line,(5,950), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,0),7)             #Uncomment these lines to print text on image
    #cv2.putText(finalBlue,line,(5,950), cv2.FONT_HERSHEY_SIMPLEX, 1,(255,255,255),2) 
    print line
    return finalBlue

if __name__ == '__main__':
    run_caffe()
    input = cv2.imread(sys.argv[1])
    input = input[0:1924, 0:1914]  #2592x1944   #crop photo to 2000x1940 (Removes camera lens from image)
    final = superPixel(input)
    #cv2.imwrite('out.jpg', final)  #Uncomment to save thresholded image.
    print 'Done.'
