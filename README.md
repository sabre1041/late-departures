# Late Departures

This repository contains a few applications for creating a demonstration of
stream processing flight departure information using Apache Kafka, Apache
Spark, and OpenShift.

## Prerequisites

To run this demonstration you will need an OpenShift project and an instance
of Apache Kafka deployed in that project. If you not familiar with OpenShift,
please see the
[getting started section](https://docs.openshift.org/latest/getting_started/index.html)
of their documentation. To deploy Kafka in your OpenShift project please see
the [Strimzi project](http://strimzi.io/) as an excellent resource for
deployment options.

## Architecture

This diagram shows a high level overview of the components and data flow which
exist in this application pipeline.

![late-departures architecture](architecture.svg)

The `air-traffic-control` application will broadcast flight departure
information that is contained within the `data.csv` file in its directory.
These details will be sent to a topic(eg "Topic 1") on a Kafka broker for
distribution

The `flight-listener` application will listen to a Kafka broker for messages
on a specified topic (eg "Topic 1). It will inspect any messages it receives
to determine if the flight in question has missed its scheduled departure
time. Any flight that has been found to have missed its scheduled departure
will then have its data broadcast onto a second topic (eg "Topic 2") with
the broker.
