import sys
import json
import psutil
import time
import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

class Producer:
    """
        Constructor for a kafka producer
    """
    def __init__(self, kafka_bootstrap_servers):
        self.producer = KafkaProducer(bootstrap_servers="broker:9092")

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

def get_cpu_usage():
    """
        Returns:
            float: current CPU usage percent
    """
    return psutil.cpu_percent()

# RAM 
def get_memory_usage():
    """
        Returns:
            float: current RAM usage percent
    """
    mem_stats = psutil.virtual_memory()
    mem_total = mem_stats.total
    mem_used = mem_stats.used
    mem_percent = mem_stats.percent
    return mem_percent

def get_disk_usage():
    """
        Returns:
            float: current DISK usage percent
    """
    disk_stats = psutil.disk_usage('/')
    disk_total = disk_stats.total
    disk_used = disk_stats.used
    disk_percent = disk_stats.percent
    return disk_percent

if __name__ == '__main__':
    service = sys.argv[1]
    taskID = sys.argv[2]
    kafka_bootstrap_servers = "localhost:9092"

    producer = Producer(kafka_bootstrap_servers)

    while True:
        try:
            cpu_usage = get_cpu_usage()
            mem_usage = get_memory_usage()
            disk_usage = get_disk_usage()
            producer.send("resources", taskID + " " + service + " CPU", str(cpu_usage))
            producer.send("resources", taskID + " " +  service + " RAM", str(mem_usage))
            producer.send("resources", taskID + " " +  service + " DISK", str(disk_usage))

            # Wait for 1 second before collecting and sending next data point
            time.sleep(1)
        except KeyboardInterrupt:
            print("Stopped reading resource consumption.")
