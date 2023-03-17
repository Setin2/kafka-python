from kafka import KafkaProducer
from kafka.errors import KafkaError

class Producer:
    """
        Constructor for a kafka producer
    """
    def __init__(self):
        self.producer = KafkaProducer()

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

    def send(self, topic, key, value, allow_callback=False):
        """
            Method for sending a message

            Args:
                topic (str): topic of our message
                key (str): the key of our message, genereally the taskID, the name of the service, 
                        the name of the resource separated by blank space
                value (float): the value of our message (resource consumption)
                allow_callback (bool): True if we want callbacks from our messages, False otherwise and by default
        """
        if allow_callback:
            self.producer.send(topic, bytes(value, 'utf-8'), bytes(key, 'utf-8')).add_callback(self.on_send_success).add_errback(self.on_send_error)
        else:
            self.producer.send(topic, bytes(value, 'utf-8'), bytes(key, 'utf-8'))

        # block until all async messages are sent
        self.producer.flush()