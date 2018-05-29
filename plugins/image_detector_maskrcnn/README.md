<!--
waggle_topic=Waggle/Node/Plugins
-->

# Pedestrian and Car Detector Plugin using Mask R-CNN

_WARNING: this plugin requires packages that are not fully supported by Waggle and does not start by default_

[Mask R-CNN is very latest released machine learning method for object detection and instance segmentation on Keras and TensorFlow](https://github.com/matterport/Mask_RCNN). The first version was released on Oct. 2017, and the developer managing https://github.com/matterport/Mask_RCNN keeps adding features. Demo code is based on the codes from the git repository, version 2.0 released on Nov. 2017.

[Mask R-CNN](https://research.fb.com/wp-content/uploads/2017/08/maskrcnn.pdf) has been developed from CNN -- R-CNN -- Fast R-CNN -- Faster R-CNN -- Mask R-CNN. You can see the brief history of it in [here](https://blog.athelas.com/a-brief-history-of-cnns-in-image-segmentation-from-r-cnn-to-mask-r-cnn-34ea83205de4). The big difference of Faster R-CNN and Mask R-CNN is that Mask R-CNN works out for pixel level segmentation.

## Prerequisites:

Libraries listed below are necessary to build and compile demo code. Tensorflow works backend, and the demo code uses CPU only.

- Tensorflow 
- Keras
- python3-h5py
- skimage
- matplotlib
- scipy

### Tensorflow on armv7l:

Tensorflow does not support binaries for armv7l officially -- [Tensorflow binaries support 64bit Ubuntu / Windows / Mac system](https://www.tensorflow.org/install/install_linux). Also to install it on armv7l, it needs to use bazel to build source codes directly. Moreover, [Tensorflow support GPU when the OS is Ubuntu and using Cuda Toolkit 9.0 / cuDNN v7](https://www.tensorflow.org/install/install_linux).

In other case, [opencv dnn can use tensorflow](https://github.com/opencv/opencv/wiki/TensorFlow-Object-Detection-API) in network.

### Keras and Tensorflow:

There is a known bug when Keras and Tensorflow are used at the same time. The error occurs occationally even if all the configurations and conditions are the same:
```
Exception ignored in: <bound method BaseSession.__del__ of <tensorflow.python.client.session.Session object at 0x7f58d50ac710>>
Traceback (most recent call last):
  File "/usr/local/lib/python3.5/dist-packages/tensorflow/python/client/session.py", line 696, in __del__
  File "/usr/local/lib/python3.5/dist-packages/tensorflow/python/framework/c_api_util.py", line 30, in __init__
TypeError: 'NoneType' object is not callable
```

Even if the error message is printed out, object detection and instance segmentation had been performed and the output result had been created without a problem (in the demo, the result is a figure with masked objects). Which means the error does not affect detection performance.

### Python3-h5py

Weights for each objects are stored in a .h5 file, which is using python3-h5py, a general-purpose Python interface to the Hierarchical Data Format library, version 5. In the demo code, it uses pre-trained weights which used MS COCO dataset with 50 classes (target objects). The size of this .h5 file is 246 MB.

In other demo code to detect balloon only, the size of the weight file is 245 MB, so that the size of the class is not impact that much in terms of size of a weight file.


## Example code:

The demo code is an implementation of Mask R-CNN on Python 3, Keras, and TensorFlow. The model generates bounding boxes and segmentation masks for each instance of an object in the image. The developer said the code is based on Feature Pyramid Network (FPN) and a ResNet101 backbone, but I've checked that it uses ResNet50. If necessary, we can update it.

The author of the [git repository](https://github.com/matterport/Mask_RCNN) keeps updates the codes with new python libraries, but we are not following updates because we don't like to expand libraries if possible.

For now, it takes time about 12-14 seconds to detect objects, and 3-12 seconds to mask objects depends on the number of segmented objects in an image.


## Mask R-CNN on EP
Because it requires more then 1.5 GB memories, it cannot be loaded on XU4 (May 2018).

