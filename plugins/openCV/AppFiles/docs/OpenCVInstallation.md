OpenCV Installation on ODROID XU4
=======================
Easiest Installation method:
$> sudo apt-get update
$> sudo apt-get install libopencv-dev python-opencv

Test that you installation was successful:

$> python
>>>import cv2

You should now be able to write OpenCV code in Python!


Custom Build method:
------------------------------
$> wget http://downloads.sourceforge.net/project/opencvlibrary/opencv-unix/2.4.9/opencv-2.4.9.zip       #Or OpenCV-3.1.0
$> unzip opencv-2.4.9.zip
$> cd opencv-2.4.9
$> mkdir build
$> cd build
$> cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D WITH_CUDA=OFF -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_QT=OFF -D WITH_V4L=ON -D WITH_OPENGL=ON -D CMAKE_SHARED_LINKER_FLAGS=-Wl,-Bsymbolic ..
$> make -j8
$> sudo make install
$> sudo sh -c 'echo "/usr/local/lib" > /etc/ld.so.conf.d/opencv.conf'
$> sudo ldconfig

Perform the same test as shown above to verify that the installation was successful.
