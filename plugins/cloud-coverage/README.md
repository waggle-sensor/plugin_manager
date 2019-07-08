
<!--
waggle_topic=/plugins_and_code
-->

## Cloud Coverage Estimator

The cloud coverage estimator plugin reports percentage of cloud coverage over the image that the top camera in the waggle node produces. It reports the cloud coverage in percentage every 30 minutes. 
With the percentage of cloud coverage estimation result, the sampled images and processed binary images that describe cloud  as True and sky as False are sent.

There are adjustable parameters when desired,
* `interval` to control estimation interval in second, default is 1800 seconds
* `recording` to control if the sampled images need to be sent or not, default is `true`
