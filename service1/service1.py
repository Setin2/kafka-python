import os
import time
import sys
from kafka import KafkaProducer

class Producer:
    """
        Constructor for a kafka producer
    """
    def __init__(self, topic, kafka_bootstrap_servers):
        self.producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers)
        self.topic = topic

    def on_send_success(self, record_metadata):
        """
            Callback method for our producer thats called on a message success
        """
        print(record_metadata.topic)
        print(record_metadata.partition)
        print(record_metadata.offset)

    def on_send_error(self, excp):
        """
            Callback method for our producer thats called on a message error
        """
        log.error('I am an errback', exc_info=excp)

    def send(self, key, value, allow_callback=False):
        """
            Method for sending a message

            Args:
                key (str): the key of our message, genereally the taskID, the name of the service, 
                        the name of the resource separated by blank space
                value (float): the value of our message (resource consumption)
                allow_callback (bool): True if we want callbacks from our messages, False otherwise and by default
        """
        if allow_callback:
            self.producer.send(self.topic, bytes(value, 'utf-8'), bytes(key, 'utf-8')).add_callback(self.on_send_success).add_errback(self.on_send_error)
        else:
            self.producer.send(self.topic, bytes(value, 'utf-8'), bytes(key, 'utf-8'))

        # block until all async messages are sent
        self.producer.flush()

kafka_bootstrap_servers = "kafka-broker:9092"
topic_name = "services"

producer = Producer(topic_name, kafka_bootstrap_servers)
service_name = sys.argv[1]
task_ID = sys.argv[2]
producer.send(service_name, task_ID)

time.sleep(4)

print("hello from service1")