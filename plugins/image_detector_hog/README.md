# Processors on the Edge

Any processors running on Edge processor have to follow the rules and constraints when use the pipeline not only for avoding any issues with other processors, but also being able to process data properly.

## Minimum Requirements for Waggle Image Processor

* The pipeline is powered by RabbitMQ such that any processors will need RabbitMQ client library in their prefered programming language. We recommend the following tools (Note that JAVA is not supported by Waggle 2.8.2 or former)

[Python](https://pypi.python.org/pypi/pika)

[C++](https://github.com/alanxz/rabbitmq-c)

## Image Collector

The image collector samples frames and transfers the samples to Beehive at a pre-defined rate. The configuration is stored in `/wagglerw/waggle/image_collector.conf` and the default is as follows,

```
{'top': {
        'daytime': [('12:00:00', '23:00:00')], # 6 AM to 7 PM in Chicago
        'interval': 3600,                       # every 60 mins
        'verbose': False
    },
 'bottom': {
    'daytime': [('12:00:00', '23:00:00')], # 6 AM to 7 PM in Chicago
    'interval': 1800,                        # every 30 mins
    'verbose': False
 }
}
```

The configuration can be adjusted, but the processor must be re-run after any adjustments.
