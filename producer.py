from kafka import KafkaProducer
from kafka.errors import KafkaError


class Producer:
    def __init__(self):
        # To consume latest messages and auto-commit offsets
        self.producer = KafkaProducer()

    def on_send_success(self, record_metadata):
        print(record_metadata.topic)
        print(record_metadata.partition)
        print(record_metadata.offset)

    def on_send_error(self, excp):
        log.error('I am an errback', exc_info=excp)

    def send(self, key, value):
        # produce asynchronously with callbacks
        self.producer.send('my-topic', bytes(value, 'utf-8'), bytes(key, 'utf-8')).add_callback(self.on_send_success).add_errback(self.on_send_error)

        # block until all async messages are sent
        self.producer.flush()