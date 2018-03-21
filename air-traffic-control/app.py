import argparse
import datetime
import io
import json
import logging
import os
import time

from kafka import KafkaProducer


def read_line(sourcefile, headings):
    """read a line from the csv file and return a dict"""
    line = sourcefile.readline()
    line = line.strip('\n')
    ret = {i[0].lower(): i[1] for i in zip(headings, line.split(','))}
    return ret


def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('topic={}'.format(args.topic))
    # logging.info('rate={}'.format(args.rate))

    logging.info('opening data source')
    sourcefile = open('data.csv')
    headings = sourcefile.readline().strip('\n')
    headings = headings.split(',')


    logging.info('creating kafka producer')
    producer = KafkaProducer(bootstrap_servers=args.brokers)

    done = False
    currentflight = None
    # we set the date to a known time that matches our data set here. as we
    # will simulate the flights departing we will advance this time to keep
    # track of the simulated day.
    currenttime = datetime.datetime(2015, 1, 1)
    oneminute = datetime.timedelta(minutes=1)
    while not done:
        if currentflight is None:
            currentflight = read_line(sourcefile, headings)
        departuretime = datetime.datetime(
                int(currentflight['year']),
                int(currentflight['month']),
                int(currentflight['day']),
                hour=int(currentflight['departure_time'][:2]),
                minute=int(currentflight['departure_time'][2:]))
        scheduledtime = datetime.datetime(
                int(currentflight['year']),
                int(currentflight['month']),
                int(currentflight['day']),
                hour=int(currentflight['scheduled_departure'][:2]),
                minute=int(currentflight['scheduled_departure'][2:]))
        if departuretime >= currenttime or scheduledtime >= currenttime:
            logging.info('sending flight info for '
                         + currentflight['airline']
                         + currentflight['flight_number'])
            producer.send(args.topic, str.encode(json.dumps(currentflight)))
            currentflight = None
        time.sleep(1.0)
        currenttime += oneminute
    logging.info('finished sending source data')


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    # args.rate = get_arg('RATE', args.rate)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting kafka-openshift-python emitter')
    parser = argparse.ArgumentParser(description='emit some stuff on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='localhost:9092')
    parser.add_argument(
            '--topic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='bones-brigade')
    # parser.add_argument(
    #         '--rate',
    #         type=int,
    #         help='Lines per second, env variable RATE',
    #         default=3)
    args = parse_args(parser)
    main(args)
    logging.info('exiting')
