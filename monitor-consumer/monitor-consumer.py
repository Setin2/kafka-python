#import torch
import os
import json
#import network
import database
import datetime
import numpy as np
#from torch.optim import Adam
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka import KafkaConsumer
import matplotlib.pyplot as plt
from kafka.errors import KafkaError
from matplotlib.pyplot import plot, draw, show, ion

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

def main():
    run_time = 0
    #plot_real = Pie_Plot()
    #plot_predicted = Pie_Plot()
    #plot = Plot()

    host, port = os.getenv("POSTGRES_HOST").split(":")
    dbname = os.getenv("POSTGRES_NAME")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

    producer = Producer("services", kafka_bootstrap_servers)
    consumer = KafkaConsumer("resources", "resources_group", bootstrap_servers=kafka_bootstrap_servers)
    data_base = database.Database(host, port, dbname, user, password)
    #model = load_model()
    for message in consumer:
        run_time += 1

        # read the message from the kafka producer
        # services is a string representation of a list, so we will need to turn it into a list before using it
        value = message.value.decode("utf-8")
        if value == "TERMINATE":
            print("send3", flush=True)
            producer.send("STOP", "STOP")
            break
        services, taskID, service, resource = message.key.decode("utf-8").split(":")
        services = eval(services)

        data_base.insert_metric(taskID, service, resource, value)
        print(message.key.decode("utf-8"), flush=True)

        # get for how long we have been running this task for in seconds
        start_time = data_base.get_start_time_for_task(taskID)[0]
        run_time = (datetime.datetime.utcnow().replace(microsecond=0) - start_time).total_seconds()

        # get the expected usage given our model
        # first we have to translate all the services/resources names to IDs
        serviceID = data_base.get_ID_from_name(0, service)
        resourceID = data_base.get_ID_from_name(1, resource)
        for i, service in enumerate(services):
            services[i] = data_base.get_ID_from_name(0, service)
        inputs = services + [serviceID] + [resourceID] + [run_time]
        #inputs = torch.tensor(inputs, dtype=torch.float32)
        #prediction = model(inputs).data
        #prediction = np.asarray(prediction)[0]

        # visualize the actual and the predicted resource usage for this service-resource pair
        #plot_real.update(resource, float(value))
        #plot_predicted.update(resource, prediction)
        #plot.update(resource, float(value), prediction)

if __name__ == '__main__':
    main()