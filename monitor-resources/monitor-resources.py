import os
import sys
import json
import time
#import torch
import psutil
#import network
import producer
import datetime
import database
import numpy as np
#from torch.optim import Adam
import matplotlib.pyplot as plt
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from matplotlib.pyplot import plot, draw, show, ion

class Pie_Plot():
    """
        Class for initializing a figure with 4 plots (for 4 resources which can be changed later)
        The figures are pie charts
    """
    def __init__(self):
        self.labels = ['Used', 'Available']
        self.fig, self.axes = plt.subplots(2, 2)
        self.axes = self.axes.flatten()
        plt.ion()
        for i, ax in enumerate(self.axes):
            ax.pie([50, 50], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title(['CPU', 'RAM', 'DISK', 'None'][i])
        plt.pause(0.001)
        plt.show()

    def update(self, key, value):
        """
            Update one of the 4 plots

            Args:
                key (str): the resource associated with the plot (CPU, RAM or DISK for now)
                value (float): the new value of the resource
        """
        if "CPU" in key:
            index = 0
        elif "RAM" in key:
            index = 1
        elif "DISK" in key:
            index = 2
        else:
            return
        
        ax = self.axes[index]
        ax.clear()
        ax.pie([value, 100-value], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        ax.set_title(['CPU', 'RAM', 'DISK'][index])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

class Plot():
    """
        Class for initializing a figure with 4 plots (for 4 resources which can be changed later)
        Each plot has 2 lines. Blue represents the actual usage of the resource while red represents the predicted usage.

        Args:
            n (int): the range of all the plots, only the last n data points will be shown
    """
    def __init__(self, n=10):
        plt.ion()
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        self.fig.subplots_adjust(left=0.2, wspace=0.6, hspace=0.6)
        self.ax1.set_title('CPU')
        self.ax2.set_title('RAM')
        self.ax3.set_title('DISK')

        self.plots = {
            "CPU": (self.ax1, [], []),
            "RAM": (self.ax2, [], []),
            "DISK": (self.ax3, [], []),
        }

        self.n = n

    def update(self, key, value, predicted_value):
        """
            Update one of the 4 plots

            Args:
                key (str): the resource associated with the plot (CPU, RAM or DISK for now)
                value (float): how much of that resource is being used
                predicted_value (float): how much of that resource our model predicts we would use
        """
        ax, data, predicted_data = self.plots[key]

        data.append(value)
        predicted_data.append(predicted_value)

        ax.clear()
        ax.plot(data[-self.n:], color="blue")
        ax.plot(predicted_data[-self.n:], color="red")

        self.ax1.set_title('CPU')
        self.ax2.set_title('RAM')
        self.ax3.set_title('DISK')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.show()

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

def load_model():
    """
        Load the model we (hopefully) previously trained

        Returns:
            network.ServiceValuePredictor: the trained model in evaluation mode
    """
    #model = network.ServiceValuePredictor(input_size=1)
    #optimizer = Adam(model.parameters(), lr=0.001)
    #model.load_model(optimizer)
    return #model

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

        #plot_real.update(resource, float(value))
        #plot_predicted.update(resource, prediction)
        #plot.update(resource, float(value), prediction)

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

#plot_real = Pie_Plot()
#plot_predicted = Pie_Plot()
#plot = Plot()

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