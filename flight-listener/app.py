"""listen for flight info on a kafka topic"""

import argparse
import datetime
import json
import os

import kafka
import pyspark
from pyspark import streaming
from pyspark.streaming import kafka as kstreaming


class FlightStreamProcessor():
    """list for flight info, rebroadcasting the late departures"""
    def __init__(self, input_topic, output_topic, servers, duration):
        """Create a new StreamProcessor

        Keyword arguments:
        input_topic -- Kafka topic to read messages from
        output_topic -- Kafka topic to write message to
        servers -- A list of Kafka brokers
        duration -- The window duration to sample the Kafka stream in
                    seconds
        """
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.servers = servers
        self.spark_context = pyspark.SparkContext(
            appName='flight-listener')
        self.streaming_context = streaming.StreamingContext(
            self.spark_context, duration)
        self.kafka_stream = kstreaming.KafkaUtils.createDirectStream(
            self.streaming_context,
            [self.input_topic],
            {'bootstrap.servers': self.servers})

    def configure_processing(self):
        """Configure the processing pipeline

        This function contains all the stream processing
        configuration that will affect how each RDD is processed.
        It will be called before the stream listener is started.
        """
        def process_data(rdd):
            """look for late flights and republish"""
            producer = kafka.KafkaProducer(bootstrap_servers=self.servers)
            for r in rdd.collect():
                try:
                    record = r.encode('ascii', 'backslashreplace')
                    data = json.loads(record)
                    departuretime = datetime.datetime(
                            int(data['year']),
                            int(data['month']),
                            int(data['day']),
                            hour=int(data['departure_time'][:2]),
                            minute=int(data['departure_time'][2:]))
                    scheduledtime = datetime.datetime(
                            int(data['year']),
                            int(data['month']),
                            int(data['day']),
                            hour=int(data['scheduled_departure'][:2]),
                            minute=int(data['scheduled_departure'][2:]))
                    if departuretime > scheduledtime:
                        producer.send(self.output_topic, record)
                except Exception as e:
                    print('Error sending collected RDD')
                    print('Original exception: {}'.format(e))
            producer.flush()

        messages = self.kafka_stream.map(lambda m: m[1])
        messages.foreachRDD(process_data)

    def start_and_await_termination(self):
        """Start the stream processor

        This function will start the Spark-based stream processor,
        it will run until `stop` is called or an exception is
        thrown.
        """
        self.configure_processing()
        self.streaming_context.start()
        self.streaming_context.awaitTermination()

    def stop(self):
        """Stop the stream processor"""
        self.streaming_context.stop()


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.input_topic = get_arg('KAFKA_INTOPIC', args.input_topic)
    args.output_topic = get_arg('KAFKA_OUTOPIC', args.output_topic)
    return args


def main():
    """The main function

    This will process the command line arguments and launch the main
    Spark/Kafka monitor class.
    """
    parser = argparse.ArgumentParser(
        description='process data with Spark, using Kafka as the transport')
    parser.add_argument(
        '--in', dest='input_topic',
        help='the kafka topic to read data from, env variable: KAFKA_INTOPIC')
    parser.add_argument(
        '--out', dest='output_topic',
        help='the kafka topic to publish data to, env variable: '
        'KAFKA_OUTTOPIC')
    parser.add_argument(
        '--brokers', help='the kafka brokers, env variable: KAFKA_BROKERS')
    args = parse_args(parser)

    processor = FlightStreamProcessor(
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        servers=args.brokers,
        duration=30)

    processor.start_and_await_termination()


if __name__ == '__main__':
    main()
