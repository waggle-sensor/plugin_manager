Caffe installation instructions for Odroid XU4
===========================
(Please note that this document details how to install the CPU-only version of Caffe. 
Caffe is built on the CUDA library, which allows for GPU processing on NVIDIA GPUs only. 
Because the XU4 is equipped with a Mali GPU, it is not CUDA compatible and is not able to perform GPU processing.) 
-----------------------------------------------------------------------------------------------------------------------------------------------------------
1). Install the general dependencies:

$> sudo apt-get install libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler
$> sudo apt-get install --no-install-recommends ddlibboost-all-dev
$> sudo apt-get update
$> sudo apt-get install libatlas-base-dev
$> sudo apt-get install python-dev
$> sudo apt-get install libgflags-dev libgoogle-glog-dev liblmdb-dev

After performing these steps, reboot your odroid with sudo reboot

2). Download Caffe Source code:

$> git clone https://github.com/BVLC/caffe.git
$> cd caffe
$> cp Makefile.config.example Makefile.config

3). Make the following changes to Makefile.config:

(Note: The directories specified in this section may be different than the ones you have on your system. 
This is fine, just be sure that you can find the specified files in these directories, and that you have updated the Makefile.config accordingly.)

1. Ensure that the line “CPU_ONLY := 1” (Line 8) is UNcommented.
2. Ensure that the paths variables of various python files are correct. 
PYTHON_INCLUDE and PYTHON_LIB will all need to point to specific directories (Lines 64/65 and 79). In this case, the Makefile.config should look similar to:

-------------------------Sample of Makefile.config---------------------------------
# We need to be able to find Python.h and numpy/arrayobject.h. 
PYTHON_INCLUDE := /usr/include/python2.7 \ 
                /usr/include/python2.7/numpy
...
# We need to be able to find libpythonX.X.so or .dylib. 
PYTHON_LIB := /usr/lib/arm-linux-gnueabihf
-------------------------End of Makefile.config sample-----------------------------

Verify that the following files exist in their respective directories before proceeding. If not, locate the file(s) and make the changes to the config.

python.h ==> /usr/include/python2.7     
numpy/arrayobject.h ==> /usr/include/python2.7/numpy
libpython2.7.so ==> /usr/lib/arm-linux-gnueabihf

3). Build Caffe (This step could take about an hour):

$> make all -j8
$> make test -j8
$> make runtest

(If errors are encountered, you may have forgotten to install a particular library or dependency. Download the needed files, then make clean and start the make process again.)

4). Enable Caffe in Python:

$> make pycaffe
$> sudo apt-get install python-skimage python-protobuf python-pydot python-pandas
$> cd caffe/python
$> python
>>> import caffe

__If no errors are returned, the install was successful! Otherwise, you may need to go back and install a required dependency.__
