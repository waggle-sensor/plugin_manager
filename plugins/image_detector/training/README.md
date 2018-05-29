<!--
waggle_topic=IGNORE
-->

# How to Train Object Detector with Tensorflow's Object Detection API

This given example is showing how to add new classes or reinforce model by training a tensorflow model. In this example, it uses pre-trained Faster R-CNN resnet101 model using COCO dataset and [Oxford Pet dataset](http://www.robots.ox.ac.uk/~vgg/data/pets/) to add names of dogs and cats in the list of detection.

## Training

### Prerequisites:

**First, make sure that you have protobuf.** The latest protobuf on May 2018 is v3.2.0:
```
curl -OL https://github.com/google/protobuf/releases/download/v3.2.0/protoc-3.2.0-linux-x86_64.zip
unzip protoc-3.2.0-linux-x86_64.zip -d protoc3

# Move protoc to /usr/local/bin/
sudo mv protoc3/bin/* /usr/local/bin/

# Move protoc3/include to /usr/local/include/
sudo mv protoc3/include/* /usr/local/include/
```

Now, you have protobuf. Then compile the protobuf where you will train a model. 
```
protoc object_detection/protos/*.proto --python_out=.
```

Add *slim* folder as a basic python path.
```
export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
```

Or you can add 
```
cd /PATH/TO/THE/FOLDER/PROTOBUFF/COMPILED
export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim
```
in ```~/.bashrc```.

### Training Example:

In this example, we will use [Oxford Pet dataset](http://www.robots.ox.ac.uk/~vgg/data/pets/) as the images for training.
```
wget http://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz
wget http://www.robots.ox.ac.uk/~vgg/data/pets/data/annotations.tar.gz
tar -xvf images.tar.gz
tar -xvf annotations.tar.gz
```

Now change the downloaded images and annotations to TFRecord file format. As a result, you wil get TFRecord files, ```.record``` files.

```
python3 create_pet_tf_record.py \
    --label_map_path=pet_label_map.pbtxt \
    --data_dir=/PATH/TO/PET/DATASET \
    --output_dir=/PATH/TO/OUTPUT
```

As a base model, we will use Faster R-CNN resnet101 coco.

```
wget http://storage.googleapis.com/download.tensorflow.org/models/object_detection/faster_rcnn_resnet101_coco_11_06_2017.tar.gz
tar -xvf faster_rcnn_resnet101_coco_11_06_2017.tar.gz
```

And move all the TFRecord files into the Faster R-CNN folder. Then in the folder, files listed below **MUST** be placed. Both ```graph.pbtxt``` and ```frozen_inference_graph.pb``` **MUST** be placed in the folder. Also the list of classes **MUST** be placed in the folder. [Example list](https://github.com/tensorflow/models/tree/master/research/object_detection/data) of classes are provided by tensorflow. In this example, we use [```pet_pabel_map.pbtxt```](https://github.com/tensorflow/models/blob/master/research/object_detection/data/pet_label_map.pbtxt) that are given by tensorflow.
```
frozen_inference_graph.pb
graph.pbtxt
model.ckpt.data-00000-of-00001
model.ckpt.index
model.ckpt.meta
pet_train.record
pet_label_map.pbtxt
```

[Configuration files](https://github.com/tensorflow/models/tree/master/research/object_detection/samples/configs) for some base models are also provided by tensorflow. In this case, we will use [```faster_rcnn_resnet101_pet.config```](https://github.com/tensorflow/models/blob/master/research/object_detection/samples/configs/faster_rcnn_resnet101_coco.config) provided by tensorflow. You need to change path written in the configuration file as **PATH_TO_BE_CONFIGURED** to where the files are exist.

When you start train:
```
python3 train.py \
    --pipeline_config_path=/PATH/TO/faster_rcnn_resnet101_pets.config \
    --train_dir=train_result
```
it will take few hours to days depends on specifications of the computer you are using for this training.

To evaluate the trained model, you can use any of object detection code for example [this](https://github.com/waggle-sensor/plugin_manager/blob/master/plugins/image_detector/training/tf_test.py), but you can also use:
```# From the tensorflow/models/ directory
python3 eval.py \
    --pipeline_config_path=/PATH/TO/faster_rcnn_resnet101_pets.config \
    --checkpoint_dir=train_result \
    --eval_dir=eval_result
```

You can see the train result and evaluation result through [tensorboard](https://www.tensorflow.org/programmers_guide/summaries_and_tensorboard).


## Use your own dataset for training: Creating Dataset

Ultimately, we need to use our own datasets for our own model. Then how to use our own set of data? You can get detailed information from the [tensorflow git repo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/using_your_own_dataset.md).

Basically, your dataset **MUST** follows [TFRecord file format](https://www.tensorflow.org/api_guides/python/python_io#tfrecords_format_details) because Tensorflow Object Detection API requires it. For the PASCAL VOC dataset and Oxford Pet Dataset, tensorflow have [ready-made scripts](https://github.com/tensorflow/models/tree/master/research/object_detection/dataset_tools) to convert the images into TFRecord file formoat.

### Collecting Data and Creating TFRecord file:

If you will use your own dataset, you need to crop images and annotate them. 

You can use [LabelImg](https://github.com/tzutalin/labelImg). With the annotating tool, annotations are saved in XML files as PASCAL VOC format. The tool requires **Python 3** and **Qt5**.

With your dataset, you can generate your own TFRecord file through TFRecord convert scripts. There are some ready-made [TFRecord convert scripts](https://github.com/tensorflow/models/tree/master/research/object_detection/dataset_tools). If the images follow PASCAL VOC dataset format, then **you can follow [create_tf_record.md](https://github.com/waggle-sensor/plugin_manager/blob/master/plugins/image_detector/training/create_tf_record.md).**

### Training:
With the image and TFRecord file, you can train models by 
```
python3 train.py \
    --pipeline_config_path=/PATH/TO/CONFIGURATION/FILE \
    --train_dir=train_result
```
as explained [above](https://github.com/waggle-sensor/plugin_manager/blob/master/plugins/image_detector/training/README.md#training-example). And for more example code, refer [tensorflow/model repo](https://github.com/tensorflow/models)

## Things we can try..
* Total number of classes of Faster R-CNN resnet101 coco model is 90. But id 78-81 are microware, over, toaster, and sink what we will never target to detect. So we can try overload new classes, such as cloud, sun, or moon. Not yet tested if the previous classes can be weakened and new on be strengthened.
* It is really time consumming and none of tensorflow users recommands, but we can remove all classes and weights and start training from scratch.


