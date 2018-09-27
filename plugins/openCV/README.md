# Detailed Installation

A comprehensive step by step guide to installing Caffe and OpenCV. 

To see a more concise version please see:

[CaffeInstallation.md](https://github.com/waggle-sensor/plugin_manager/edit/master/plugins/openCV/AppFiles/docs/CaffeInstallation.md)

[OpenCVInstallation.md](https://github.com/waggle-sensor/plugin_manager/edit/master/plugins/openCV/AppFiles/docs/OpenCVInstallation.md)

First check your version of python by simply going to a command prompt and use the command:

`python` 

There may be compatibility issues if you are not using python 2.7, if that is the case change to python 2.7 by using the command:

`alias python=python2`

## OpenCV Installation

Use the command:

`sudo apt-get update`

Then install openCV using the command: 

`sudo apt-get install libopencv-dev python-opencv`

Test by using the command:

`python`

and then type in :

`import cv2`

There should be no errors.

## Caffe Installation (CPU-only version)

As the XU4 Edge Processor does not support CUDA, we will be installing a CPU-only version of Caffe.

### Begin by installing the following dependencies:

`sudo apt-get install libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler`

`sudo apt-get install --no-install-recommends libboost-all-dev`

`sudo apt-get update`

`sudo apt-get install libatlas-base-dev`

`sudo apt-get install python-dev`

`sudo apt-get install libgflags-dev libgoogle-glog-dev liblmdb-dev`

As a precaution you can restart to make sure all the dependencies are installed using the command:

`reboot`

### Downloading Caffe source code

Next we will be downloading the Caffe source code, so go to a file path you are comfortable with (your user directory is fine ex: /home/username) and use the command to clone the repo into your local directory:

`git clone https://github.com/BVLC/caffe.git`

Once it is finished, go into the directory using: 

`cd caffe`

Before we start copy the configuration using the command:

`cp Makefile.config.example Makefile.config`

### Configuring Makefile.config

You will now make changes to the Makefile.config, so go into the file using the command:

`nano Makefile.config`

Now we are going to make four changes to the Makefile.config, I will give the line number of each line you will be changing, you can check what line you are hovering over by using CTRL+c  in nano. 

* Line 8: Uncomment the line “CPU_ONLY := 1” by deleting the pound/hashtag symbol in front of the line.

* Line 69-70: Verify these lines by going to the directory using the command:

`cd /usr/include/python2.7` 

Use the command:

`ls` 

Make sure the file Python.h exists in the directory, if not use the command:

`locate Python.h`

Then replace the “/usr/include/python2.7” portion of line 69 after PYTHON_INCLUDE:= with the output of the locate command.

We will now do the same with line 70, so go to the directory using the command:

`cd /usr/include/python2.7/numpy`

If this directory does not exist you may need to install numpy, so first use the command:

`sudo apt-get install python-pip`

Then install numpy using the command:

`sudo pip install numpy`

Use the command: 

`ls`

Make sure the file arrayobject.h exists in the directory, if not use the command:

`locate arrayobject.h`

Then replace line 70 with the output of the command that looks like (remember to keep the indentation) “/usr/lib/python2.7/dist-packages/numpy/core/include/numpy/arrayobject.h”
* Line 84: Must be able to find libpython2.7, so use the command:

`locate libpython2.7.so`

There will be multiple outputs, look for an output that ends with libpython2.7.so, for example:

“/usr/lib/python2.7/config-x86_64-linux-gnu/libpython2.7.so”

Replace the filepath in Line 84 after PYTHON_LIB := with the correct output.

Save the file using CTRL+o, press enter, then exit using CTRL+x

### Building Caffe

Use cmake: 

First make a build directory using the command:

`mkdir build`

Go into the directory using the command:

`cd build`

Now use the following commands to build/make:

`cmake ..`

`make all`

`make install`

`make runtest`

There should be no errors, if there are make sure you review the guide, especially the first portion where you installed dependencies. 

### Enabling Caffe in Python 

At this point you should still be in the /caffe/build directory, now use the command:

`make pycaffe`

Install dependencies using the command:

`sudo apt-get install python-skimage python-protobuf python-pydot python-pandas`

Back out of the build directory using the command: 

`cd ..`

Then go into the python directory using the command:

`cd python`

Test by using the command:

`python`

and then type in:

`import caffe`

There should be no errors, if there are review the guide and make sure you are in the /caffe/python directory. 

## Using CloudApp.py

Go back to your user directory (or where ever you would like to save the repo) and clone the plugin_manager directory using the command: 

`git clone https://github.com/waggle-sensor/plugin_manager.git`

Once finished use the following command to copy the CloudApp.py and AppFiles folder to the /caffe/python directory (you can do this more intuitively using file manager): 

`cp /home/username/plugin_manager/plugins/openCV /home/username/caffe/python`

Replacing username with your own username, if you did not save these directories into your home folder then adjust accordingly, you can go into the folder with openCV and /caffe/python and use the command to get the full filepath:

`pwd`

You are ready for use, go to the python directory inside the caffe directory using the command:

`cd /caffe/python` 

Go into AppFiles using the command:

`cd AppFiles`

Go into images using the command:

`cd images` 

Type this in to view the list of images: 

`ls`

Choose an image and then use the command:

`cp /home/username/caffe/python/AppFiles/images/imagename.jpg /home/username/caffe/python`

Replacing username with your username and imagename.jpg with your image. Again you may have different filepaths so adjust accordingly. 

Go back to the /caffe/python directory and you can execute CloudApp.py using the command:

`python CloudApp.py imagename.jpg`

Replacing imagename.jpg with the image you have copied over to this directory. If the output is correct and there are no errors, congratulations! 
