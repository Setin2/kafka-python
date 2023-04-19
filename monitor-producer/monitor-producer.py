import os
import sys
import json
import time
import psutil
import producer
import datetime
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError

def get_cpu_usage():
    """
        Returns:
            float: current CPU usage percent
    """
    process = psutil.Process()  # get the current process
    return process.cpu_percent()

# RAM 
def get_memory_usage():
    """
        Returns:
            float: current RAM usage percent
    """
    process = psutil.Process()  # get the current process
    mem_stats = process.virtual_memory()
    mem_total = mem_stats.total
    mem_used = mem_stats.used
    mem_percent = mem_stats.percent
    return mem_percent

def get_disk_usage():
    """
        Returns:
            float: current DISK usage percent
    """
    process = psutil.Process()  # get the current process
    disk_stats = process.disk_usage('/')
    disk_total = disk_stats.total
    disk_used = disk_stats.used
    disk_percent = disk_stats.percent
    return disk_percent

def send_metrics(message):
    """
        Produce a message with the metrics for the given service to the "resources" topic.

        Args:
            message (saf): sadsad
    """
    global stop_monitoring
    message_type = message.key.decode("utf-8")

    # task is done, wait for next task
    if "HALT" in message_type:
        return
    # order is finished, notify the monitor-consumer
    if "STOP" in message_type:
        producer.send("STOP", "STOP")
    # monitor-consumer has closed down, we stop this script as well
    elif "TERMINATE" in message_type:
        stop_monitoring = True
    # a task is running, get its resource consumption and send it to the monitor-consumer
    else:
        required_tasks, task, orderID = message.value.decode("utf-8").split(":")
        cpu_usage = get_cpu_usage()
        mem_usage = get_memory_usage()
        disk_usage = get_disk_usage()
        producer.send(required_tasks + ":" + orderID + ":" + task + ":CPU", str(cpu_usage))
        producer.send(required_tasks + ":" + orderID + ":" +  task + ":RAM", str(mem_usage))
        producer.send(required_tasks + ":" + orderID + ":" +  task + ":DISK", str(disk_usage))

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
orderID = sys.argv[1]
producer = producer.Producer("resource" + orderID, kafka_bootstrap_servers)
consumer = KafkaConsumer("task" + orderID, bootstrap_servers=kafka_bootstrap_servers)

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