<!--
waggle_topic=/plugins_and_code
-->

# Image Processing Example

## Minimum Requirements for Waggle Image Processor

* The pipeline is powered by RabbitMQ such that any processors will need RabbitMQ client library provided in their prefered programming language. We recommend the following tools (Note that JAVA is currently not supported by Waggle)

[Python](https://pypi.python.org/pypi/pika)

[C++](https://github.com/alanxz/rabbitmq-c)

## Example Processor

The example processor provides basic information of a captured frame. The basic information includes average color and normalized (0-255) histogram of R, G, B channels of the frame. Every 5 bins are grouped: 51 bins represent the range of 255 bins. Length of histogram in each channel is (255 / 15 =) 17 bytes due to the limit of Waggle subpacket length. The processor runs 24 hours a day and outputs every 5 minutes. The plugin uses sensor_ID `0xA0` to send data to Beehive.

The following shows human readable form of the information,

```
image_average_color_b 128
image_average_color_g 128
image_average_color_r 127
image_device b
image_histogram_b 07689f83a886a2735fa08e71622c242fff
image_histogram_g 087891776ec967777e7e7e6444392d21ff
image_histogram_r 0e6f93697a7c6771878f68452528251eff
```
