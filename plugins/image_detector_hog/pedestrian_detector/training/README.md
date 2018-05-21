# Trainer for pedestrian detection

This document covers 1) collections of positive and negative images by cropping sample images, 2) training a classifier, and 3) performing hard-negative-mining for the classifier.

# Requirements

* OpenCV 3.2.0 or higher (including Python wrapper)
* A Waggle camera
* Numpy 1.13 or higher

# Steps

1. Collect sample images

Take images from an attached Waggle camera. Collecting more than 1,000 images is advised. As a person will manually do cropping to annotate positive images from the sample images, the sample images would need to be resized to fit to the screen for the person to see them for the job. Do the following,

```bash
$ crop_images.py --image=/PATH/TO/SAMPLE_IMAGES --out=/PATH/TO/POSITIVE_IMAGES --screen-width=1380 --screen-height=768
```

An OpenCV window will appear to show the sample images. One mouse click on the window will show you a rectangle at the left-top conner. Drag & drop with left click will move the rectangle, while the same operation with right click will scale up and down the rectangle with a fixed ratio. To crop pedestrians, put the pedestrian you are trying to crop into the rectangle and press __c__. Try to put the person at the center of the rectangle for better result. The cropped image will automatically be resized into 64 X 128 (width x height) and stored into the path of positive images. After cropping all pedestrians of the image, press __q__ to move to next sample image. Pressing __z__ will exit the program.

Put non-scaled images that have no pedestrian into the /PATH/TO/NEGETIVE_IMAGES. Putting different images in terms of angle, brightness, and shade is advised.

2. Run trainer for classifier

First of all, make files that respectively contain a list of positive and negative images.

```bash
$ ls /PATH/TO/POSITIVE_IMAGES > pos.lst
$ mv pos.lst /PATH/TO/POSITIVE_IMAGES
$ ls /PATH/TO/NEGATIVE_IMAGES > neg.lst
$ mv neg.lst /PATH/TO/NEGATIVE_IMAGES
```

To train a classifier for pedestrian detection,

```bash
$ cd /PATH/TO/TRAINER
$ ./trainer.py -pd=/PATH/TO/POSITIVE_IMAGES/ -p=pos.lst -nd=/PATH/TO/NEGATIVE_IMAGES/ -n=neg.lst
$ ls -l my_people_detector.xml 
-rw-rw-r-- 1 waggle waggle 130643864 Jul  3 13:29 my_people_detector.xml
$ cp my_people_detector.xml /PATH/TO/PEDESTRIAN_CLASSIFIER
```

If you need to add existing training set when train the classifier, do the following,

```bash
$ ./trainer.py -pd=/PATH/TO/POSITIVE_IMAGES/ -p=pos.lst -nd=/PATH/TO/NEGATIVE_IMAGES/ -n=neg.lst -b=/PATH/TO/BINARY_IMAGES -bl=/PATH/TO/LABELS_OF_THE_BINARY_IMAGES
```

Make sure that the binary images have the same window size with the positive images.

3. Test the classifier

* If the classifier runs standalone mode, it connects to the source camera directly to get images and outputs any detected pedestrians in an image to OUTPUT_PATH.

```bash
$ cd /PATH/TO/PEDESTRIAN_CLASSIFIER
$ ./pedestrian_classifier.py -c=my_people_detector.xml -s /PATH/TO/CAMERA/DEVICE -o /PATH/TO/OUTPUT
```

* If the classifier runs along with RabbitMQ and other producers (e.g., waggle pipeline services), it connects to the source exchange with a routing key and outputs the source image and detection results to the exchange with a different routing key. In this case, it is assumed that there are image producer and exporter for the classifier. To test the classifier and collect results,

```bash
$ cd /PATH/TO/PEDESTRIAN_CLASSIFIER
$ ./pedestrian_classifier.py -c=my_people_detector.xml --rabbitmq-exchange NAME_OF_EXCHANGE --rabbitmq-routing-input INPUT_ROUTING_KEY --rabbitmq-routing-output OUTPUT_ROUTING_KEY
// or
# after setting arguments correctly...
$ systemctl (re)start waggle-image-pedestrian-detector.service
```

4. Hard-negative mining (Optional)

If the results of the detection contain many false positives, meaning that the detector recognized things that are actually not pedestrian, hard-negative mining is required for the classifier.