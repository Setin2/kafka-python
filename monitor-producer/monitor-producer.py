import os
import sys
import json
import psutil
import time
import datetime
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError

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

def send_metrics(message):
    global stop_monitoring
    taskID = message.value.decode("utf-8")

    if "TERMINATE" in taskID:
        producer.send("TERMINATE", "TERMINATE")
    elif "STOP" in taskID:
        stop_monitoring = True
    else:
        service_list, service = message.key.decode("utf-8").split(":")
        cpu_usage = get_cpu_usage()
        mem_usage = get_memory_usage()
        disk_usage = get_disk_usage()
        print(service_list + " " + taskID + " " + service + ":CPU", str(cpu_usage), flush=True)
        producer.send(service_list + ":" + taskID + ":" + service + ":CPU", str(cpu_usage))
        producer.send(service_list + ":" + taskID + ":" +  service + ":RAM", str(mem_usage))
        producer.send(service_list + ":" + taskID + ":" +  service + ":DISK", str(disk_usage))

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
producer = Producer("resources", kafka_bootstrap_servers)
consumer = KafkaConsumer("services", "services_group", bootstrap_servers=kafka_bootstrap_servers)

# the message from the current job we are monitoring
current_message = None
stop_monitoring = False
while not stop_monitoring:
    # check to see if we got a new message
    new_message = consumer.poll(0.1)
    
    # if not, we send metrics for current service
    if not new_message and current_message is not None:
        send_metrics(current_message)

    # else, we check to see if we need to terminate monitoring, or update the current service to this new one
    elif new_message:
        # we need to loop thorugh the partition message
        for tp, messages in new_message.items():
            for message in messages:
                current_message = message
                send_metrics(current_message)
    time.sleep(0.5)
