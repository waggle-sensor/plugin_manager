# Waggle Cloud Detection Documentation

1). CaffeInstallation.md:       Steps taken to install CPU only Caffe on ODROID XU4.

2). OpenCVInstallation.md:      Steps taken to install OpenCV 3 on ODROID XU4

3). AppFiles:                   CloudApp.py executable, sample images, required files
        -.caffemodel, mean.npy, synset_words.txt, and deploy.prototxt must be in same directory as CloudApp.py

4). Makefile.config:       The Makefile used to build Caffe


Need to have Caffe built with pycaffe, openCV, and skimage:
CloudApp.py and AppFiles need to be placed in same directory.
Either run both in caffe/python directory, or after running

```
export PYTHONPATH=/home/......./caffe/python:$PYTHONPATH
```

Steps For Using Caffe:
----------------------
1). Prepare data - Put training images and validation images into their own folders. 'Train.txt' and 'Val.txt' should consist
    of thee full paths to each image in the directories with the index of 'synset_words.txt' that corresponds to that image's
    label. (Run data/ilsvrc12/get_ilsvrc_aux.sh and look at files there to get an idea of the formats).

2). Use examples/imagenet/create_imagenet.sh to resize images and store as LMDB. Use examples/imagenet/make_imagenet_mean.sh
    to make mean.binaryproto, then convert to mean.npy with convert.py. Might need to edit these files to get correct paths.

3). Edit models/.../train_val.prototxt and models/.../solver.prototxt to include LMDB's and adjust design of CNN.

4). Start training:
```
./build/tools/caffe train -solver models/.../solver.prototxt
```

Some helpful links:
-------------------
https://groups.google.com/forum/#!forum/caffe-users

https://prateekvjoshi.com/2016/02/16/deep-learning-with-caffe-in-python-part-iii-training-a-cnn/

http://adilmoujahid.com/posts/2016/06/introduction-deep-learning-python-caffe/

https://software.intel.com/en-us/articles/training-and-deploying-deep-learning-networks-with-caffe-optimized-for-intel-architecture#

http://shengshuyang.github.io/A-step-by-step-guide-to-Caffe.html
