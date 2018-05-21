<!--
waggle_topic=IGNORE
-->

# Mask R-CNN for Object Detection and Segmentation

This is an implementation of [Mask R-CNN](https://arxiv.org/abs/1703.06870) on Python 3, Keras, and TensorFlow. The model generates bounding boxes and segmentation masks for each instance of an object in the image. It's based on Feature Pyramid Network (FPN) and a ResNet101 backbone.

The repository includes:
* Source code of Mask R-CNN built on FPN and ResNet101.
* Training code for MS COCO
* Pre-trained weights for MS COCO
* Jupyter notebooks to visualize the detection pipeline at every step
* ParallelModel class for multi-GPU training
* Evaluation on MS COCO metrics (AP)
* Example of training on your own dataset


## Requirements
* Python 3.4+
* TensorFlow 1.3+
* Keras 2.0.8+
* Numpy, skimage, scipy, cython, h5py


# EP Example

This is an example showing the use of Mask RCNN in a real application.
We train the model to 50 objects, which are listed in a class in the demo.py,
and then we use the generated bounding boxes, mask polygons, and labels to the objects.

## Prerequites for This Example:
1. To run this code, You MUST download pre-trained COCO weights (mask_rcnn_coco.h5) from the [releases page](https://github.com/matterport/Mask_RCNN/releases).
2. Before run this code, You MUST designate root directory of the project in the code ```demo.py```.
```
# Root directory of the project
ROOT_DIR = os.getcwd()
IMAGE_DIR =  os.path.join(ROOT_DIR, "images")
```

## Apply demo using the provided weights
Apply splash effect on an image:

```bash
python3 demo.py --image=<file path or URL>
```

The code in `demo.py` is set to train for 50K steps (50 epochs of 1000 steps each), and using a batch size of 1.
Update the schedule to fit your needs.
