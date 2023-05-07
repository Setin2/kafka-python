import os
import sys
import json
import time
import psutil
import producer
import datetime
import database
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError

def get_cpu_usage(pid):
    """
        Returns:
            float: current CPU usage percent
    """
    process = psutil.Process()  # get the current process
    return process.cpu_percent()

# RAM 
def get_memory_usage(pid):
    """
        Returns:
            float: current RAM usage percent
    """
    process = psutil.Process()  # get the current process
    mem_stats = process.memory_info()
    ram_mb = mem_stats.rss / (1024 * 1024) # get the RAM usage in MB
    ram_percent = (mem_stats.rss / psutil.virtual_memory().total) * 100 #get the RAM usage as percentage
    return ram_percent

def get_disk_usage(pid):
    """
        Returns:
            float: current DISK usage percent
    """
    process = psutil.Process()  # get the current process
    io_counters = process.io_counters() # will have shape pio(read_count=307, write_count=198, read_bytes=2011136, write_bytes=510464, read_chars=2011136, write_chars=510464)
    total_disk_io = psutil.disk_io_counters().read_bytes + psutil.disk_io_counters().write_bytes
    #read_mb = io_counters.read_bytes / (1024 * 1024)
    #write_mb = io_counters.write_bytes / (1024 * 1024)
    read_percent = (io_counters.read_bytes / total_disk_io) * 100
    write_percent = (io_counters.write_bytes / total_disk_io) * 100
    return read_percent + write_percent # toal disk usage as percentage

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
    # a task is running, get its resource consumption and send it to the monitor-consumer
    else:
        required_tasks, task, task_pid, orderID = message.value.decode("utf-8").split(":")
        task_pid = int(task_pid)
        cpu_usage = get_cpu_usage(task_pid)
        mem_usage = get_memory_usage(task_pid)
        disk_usage = get_disk_usage(task_pid)
        data_base.insert_metric(orderID, task, "CPU", cpu_usage)
        data_base.insert_metric(orderID, task, "RAM", mem_usage)
        data_base.insert_metric(orderID, task, "DISK", disk_usage)
        print("Insert: " + str(orderID) + task + "CPU" + str(cpu_usage), flush=True)

def get_expected_usage(data_base, tasks, task, resource, task_runtime):
    # get the expected usage given our model
    # first we have to translate all the tasks/resources names to IDs
    taskID = data_base.get_ID_from_name(0, task)
    resourceID = data_base.get_ID_from_name(1, resource)
    for i, task in enumerate(tasks):
        tasks[i] = data_base.get_ID_from_name(0, task)
    inputs = tasks + [taskID] + [resourceID] + [task_runtime]

    #inputs = torch.tensor(inputs, dtype=torch.float32)
    #prediction = model(inputs).data
    #prediction = np.asarray(prediction)[0]
    #return prediction

host, port = os.getenv("POSTGRES_HOST").split(":")
dbname = os.getenv("POSTGRES_NAME")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
data_base = database.Database(host, port, dbname, user, password)

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer("resource", bootstrap_servers=kafka_bootstrap_servers)

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