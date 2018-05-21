# Pedestrian detector

This processor captures any pedestrians in the captured scene. This is ```oneshot``` process that runs from start time to end time specified by the configuration file under ```/etc/waggle/image_pedestrian_detection.conf```. The processor requires a classifier trained previously. It also uses OpenCV 3.2.0 HOGDescriptor to detect pedestrian. Settings for HOGDescriptor are,

```bash
block_size = (16, 16)
block_stride = (8, 8)
cell_size = (8, 8)
n_bins = 9
derive_aperture = 1
win_sigma = 4.
histogram_norm_type = 0
l2_hys_threshold = 2.0e-01
gamma_correction = 0
n_levels = 64
```

Below is the default setting for the configuration,

```bash
conf = {
    'classifier': '/etc/waggle/pedestrian_classifier.xml',
    'start_time': time.strftime(datetime_format, time.gmtime()),
    'end_time': time.strftime(datetime_format, time.gmtime()),
    'daytime': ('00:00:00', '23:59:59'),
    'target': 'bottom',
    'interval': 1,
    'mode': MODE_BURST,
    'verbose': False
}
```
where, ```classifier``` indicates path of the classifier file, ```start_time``` and ```end_time``` represent life cycle of the processor using expression such as ```Wed Jul 26 23:06:50 GMT 2017```, ```daytime``` restricts operation hours of the processor in a day, ```target``` indicates which camera is the source, ```interval``` tells how often the processor iterates a unit step, ```verbose``` prints out some information messages during the execution. ```mode``` supports two modes: 'batch' and 'burst'. 'batch' mode only counts number of detected pedestrians during the execution and sends total number of the detection at the end of execution, whereas 'burst' mode processes each frame of the scene and puts detection information into the frame which will then be transferred to the next pipeline.