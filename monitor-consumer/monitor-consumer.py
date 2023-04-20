import os
import sys
import json
#import torch
#import network
import database
import datetime
import producer
import numpy as np
#from torch.optim import Adam
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka import KafkaConsumer
import matplotlib.pyplot as plt
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

#def load_model():
#    """
#        Load the model we (hopefully) previously trained
#
#        Returns:
#            network.ServiceValuePredictor: the trained model in evaluation mode
#    """
#    model = network.ServiceValuePredictor(input_size=1)
#    optimizer = Adam(model.parameters(), lr=0.001)
#    model.load_model(optimizer)
#    return model

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

# get environment variables
host, port = os.getenv("POSTGRES_HOST").split(":")
dbname = os.getenv("POSTGRES_NAME")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

orderID = sys.argv[1]
producer = producer.Producer("task" + orderID, kafka_bootstrap_servers)
consumer = KafkaConsumer("resource" + orderID, bootstrap_servers=kafka_bootstrap_servers)
data_base = database.Database(host, port, dbname, user, password)
curr_task = ""
task_runtime = 0
#model = load_model()
for message in consumer:
    # read the message from the kafka producer
    # tasks is a string representation of a list, so we will need to turn it into a list before using it
    value = message.value.decode("utf-8")
    # we got a termination notification
    if "STOP" in value:
        producer.send("TERMINATE", "TERMINATE")
        break
    tasks, orderID, task, resource = message.key.decode("utf-8").split(":")
    # check to see if we are monitoring a new task (we need to keep track of how long we run tasks for)
    if task is not curr_task:
        curr_task = task
        task_runtime = 0
    else: task_runtime += 1
    tasks = eval(tasks)

    data_base.insert_metric(orderID, task, resource, value)

    get_expected_usage(data_base, tasks, task, resource, task_runtime)

    # visualize the actual and the predicted resource usage for this task-resource pair
    #plot_real.update(resource, float(value))
    #plot_predicted.update(resource, prediction)
    #plot.update(resource, float(value), prediction)