## Minimum Requirements for Waggle Image Processor

* The pipeline is powered by RabbitMQ such that any processors will need RabbitMQ client library provided in their prefered programming language. We recommend the following tools (Note that JAVA is currently not supported by Waggle)

[Python](https://pypi.python.org/pypi/pika)

[C++](https://github.com/alanxz/rabbitmq-c)

## Example Processor

The example processor provides basic information of a captured frame. The basic information includes average color and normalized (0-255) histogram of R, G, B channels of the frame. Every 5 bins are grouped: 51 bins represent the range of 255 bins. Length of histogram in each channel is (255 / 5 =) 51 bytes. The processor runs 24 hours a day and outputs every 5 minutes. The plugin uses sensor_ID `0xA0` to send data to Beehive.

The following shows human readable form of the information,

```
image_average_color_b 124
image_average_color_g 134
image_average_color_r 137
image_device b
image_histogram_b 344c6163594b45484648413f3b3a3632343942527a868983734e373543566167899e989d76595e582e1b110f0f1110101519ff
image_histogram_g 0e234954647675563f2f27231f211c1d1d1c1b1f2e39383c68a3ae4d38232028405a5769889e83684d3b37403d270e101110ff
image_histogram_r 0f274d6e715f523829231f1a191a1a1a1917171d29383b3e7cac8541261c1b1d304549575b697071674a332a38572e110d0eff
```