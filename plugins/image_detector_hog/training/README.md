<!--
waggle_topic=IGNORE
-->

# Trainer for pedestrian detection

This document covers:
1) Collection of positive and negative images by cropping sample images 
2) Training a classifier
3) Performing hard-negative-mining for the classifier

# Requirements

* OpenCV 3.2.0 or higher (including Python wrapper)
* A Waggle camera
* Numpy 1.13 or higher
* plugin_manager repository

To install these requirements, first check your version of python using the command:

`python`

If it is not using python3 then switch to it by using the command:

`alias python=python3`

Then install the dependencies:

`sudo apt-get install python-pip`

`sudo pip install numpy`

`sudo pip install opencv-python`

If you have already installed these requirements and are having trouble using them in python 3, use the following commands:

`sudo python3 -m pip install numpy`

`sudo python3 -m pip install opencv-python`

Then go to a location you are comfortable with (make a repos folder if you have not already done so) and clone the plugin_manager repository:

`git clone https://github.com/waggle-sensor/plugin_manager.git`

# Steps

## 1) Collect sample images

First create a sample images folder which will hold all of your collected images:

`mkdir sample_images`

Then create a positive images folder which will be the output folder:

`mkdir positive_images`

Finally create a negative images folder which will hold pictures with no pedestrians:

`mkdir negative_images`

When /path/to/ is mentioned in the document, it needs to be replaced with the file path to your file/folder. For example if you placed positive_images in your /home/your_username then it will be /home/your_username/postive_images replacing your_username of course. In order to get the entire path, go to the targeted file/forward and use the command:

`pwd`

Take images from an attached Waggle camera. Collecting more than 1,000 images is advised. As a person will manually do cropping to annotate positive images from the sample images, the sample images would need to be resized to fit to the screen for the person to see them for the job. Do the following:

`python crop_images.py --image=/path/to/sample_images --out=/path/to/positive_images --screen-width=1380 --screen-height=768`

An OpenCV window will appear to show the sample images, here are the steps to crop the images: 
* One mouse click on the window will show you a rectangle at the left-top conner. 
* Drag and drop with left click will move the rectangle, 
* Drag and drop with right click will scale up and down the rectangle with a fixed ratio. 
* To crop pedestrians, put the pedestrian you are trying to crop into the rectangle and press __c__. Try to put the person at the center of the rectangle for better result. 
* The cropped image will automatically be resized into 64 X 128 (width x height) and stored into the path of positive images. 
* After cropping all pedestrians of the image, press __q__ to move to next sample image. 
* Pressing __z__ will exit the program.

Put non-scaled images that have no pedestrian into the /path/to/negative_images. Putting different images in terms of angle, brightness, and shade is advised.

## 2) Run trainer for classifier

First of all, make files that respectively contain a list of positive and negative images then move them to your positive_images and negative_images folders.

`ls /path/to/positive_images > pos.lst`

`mv pos.lst /path/to/positive_images`

`ls /path/to/negative_images > neg.lst`

`mv neg.lst /path/to/negative_images`

To train a classifier for pedestrian detection,

`cd /path/to/plugin_manager/plugins/image_detector_hog/training/trainer.py`

`./trainer.py -pd=/path/to/positive_images/ -p=pos.lst -nd=/path/to/negative_images/ -n=neg.lst -o my_people_detector.xml`

`ls -l my_people_detector.xml`

`cp my_people_detector.xml /path/to/plugin_manager/plugins/image_detector_hog/pedestrian_classifier.py`

If you need to add an existing training set when train the classifier, do the following,

`./trainer.py -pd=/path/to/positive_images/ -p=pos.lst -nd=/path/to/negative_images/ -n=neg.lst -b=/path/to/binary_images -bl=/path/to/labels_of_the_binary_images`

Make sure that the binary images have the same window size with the positive images.

## 3) Test the classifier

* If the classifier runs standalone mode, it connects to the source camera directly to get images and outputs any detected pedestrians in an image to OUTPUT_PATH.

`cd /path/to/plugin_manager/plugins/image_detector_hog/pedestrian_classifier.py`

`./pedestrian_classifier.py -c=my_people_detector.xml -s /path/to/camera/device -o /path/to/output`

* If the classifier runs along with RabbitMQ and other producers (e.g., waggle pipeline services), it connects to the source exchange with a routing key and outputs the source image and detection results to the exchange with a different routing key. In this case, it is assumed that there are image producer and exporter for the classifier. To test the classifier and collect results,

`cd /path/to/plugin_manager/plugins/image_detector_hog/pedestrian_classifier.py`

`./pedestrian_classifier.py -c=my_people_detector.xml --rabbitmq-exchange NAME_OF_EXCHANGE --rabbitmq-routing-input INPUT_ROUTING_KEY --rabbitmq-routing-output OUTPUT_ROUTING_KEY`

// or
# after setting arguments correctly...

`systemctl (re)start waggle-image-pedestrian-detector.service`

4. Hard-negative mining (Optional)

If the results of the detection contain many false positives, meaning that the detector recognized things that are actually not pedestrian, hard-negative mining is required for the classifier.
