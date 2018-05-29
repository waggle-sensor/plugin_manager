# Create tensorflow record (TFRecord)

## Crop images and annotate them
* Use [LabelImg](https://github.com/tzutalin/labelImg).
* You will have an ```.xml``` file for *each image* when you use [LabelImg](https://github.com/tzutalin/labelImg).
* The results are Pascal VOC dataset format.

## Create TFRecord
* Use label.pbtxt which you created and [create_tfrecord_pascal_like.py](https://github.com/waggle-sensor/plugin_manager/blob/master/plugins/image_detector/training/create_tfrecord_pascal_like.py) by
```
python3 create_tfrecord_pascal_like.py --image_dir=/PATH/TO/IMAGE/FOLDER \
    --annotations_dir=/PATH/TO/XML/FOLDER \
    --label_map_path=/PATH/TO/LABEL \
    --output_path=/PATH/FOR/OUTPUT \
```
* You will have a ```.record``` for a training.

### Example of label.pbtxt:
```
item {
  id: 1
  name: 'person'
}

iten {
  id: 3
  name: 'car'
}
```

# Then, Train a model with the record
* Refer [README.md](https://github.com/waggle-sensor/plugin_manager/blob/master/plugins/image_detector/training/README.md) and do train, for example:
```
python3 train.py \
    --pipeline_config_path=/PATH/TO/faster_rcnn_resnet101_test.config \
    --train_dir=train_result
```
