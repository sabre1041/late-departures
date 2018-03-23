# Air Traffic Controller

This application will read the flight departure data from the `data.csv` file
and replay that information on a Kafka topic.

The data contained in `data.csv` originated from the Kaggle dataset
[2015 Flight Delays and Cancellations](https://www.kaggle.com/usdot/flight-delays),
and is licensed under a
[CC0 - Public Domain](https://creativecommons.org/publicdomain/zero/1.0/) license.

## Launching on OpenShift

```
oc new-app centos/python-36-centos7~https://github.com/elmiko/late-departures.git \
  -e KAFKA_BROKERS=my-cluster-kafka:9092 \
  -e KAFKA_TOPIC=flights \
  --context-dir=air-traffic-control \
  --name=air-traffic-control
```
