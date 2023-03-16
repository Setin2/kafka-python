import torch
import network
import database
import numpy as np
from torch.optim import Adam
from kafka import KafkaConsumer
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, draw, show, ion

class Plot():
    """
        Class for initializing a figure with 4 plots (for 4 resources which can be changed later)
    """
    def __init__(self):
        self.labels = ['Used', 'Available']
        self.fig1, self.ax1 = plt.subplots(2, 2)
        plt.ion()
        self.ax1[0, 0].pie([50, 50], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        self.ax1[0, 0].axis('equal')
        self.ax1[0, 0].title.set_text('CPU')
        self.ax1[0, 1].pie([50, 50], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        self.ax1[0, 1].axis('equal')
        self.ax1[0, 1].title.set_text('RAM')
        self.ax1[1, 0].pie([50, 50], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        self.ax1[1, 0].axis('equal')
        self.ax1[1, 0].title.set_text('DISK')
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
            self.ax1[0, 0].clear()
            self.ax1[0, 0].pie([value, 100-value], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
            self.ax1[0, 0].title.set_text('CPU')
        elif "RAM" in key:
            self.ax1[0, 1].clear()
            self.ax1[0, 1].pie([value, 100-value], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
            self.ax1[0, 1].title.set_text('RAM')
        elif "DISK" in key:
            self.ax1[1, 0].clear()
            self.ax1[1, 0].pie([value, 100-value], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
            self.ax1[1, 0].title.set_text('DISK')
        # re-drawing the figure
        self.fig1.canvas.draw()
        # to flush the GUI events
        self.fig1.canvas.flush_events()

def load_model():
    """
        Load the model we (hopefully) previously trained

        Returns:
            network.ServiceValuePredictor: the trained model in evaluation mode
    """
    model = network.ServiceValuePredictor(input_size=1)
    optimizer = Adam(model.parameters(), lr=0.001)
    model.load_model(optimizer)
    return model

def main():
    run_time = 0
    consumer = KafkaConsumer("resources", "my-group", bootstrap_servers=['localhost:9092'])
    plot_real = Plot()
    plot_predicted = Plot()
    data_base = database.Database()
    model = load_model()
    try:
        for message in consumer:
            run_time += 1
            # read the message from the kafka producer
            image_ID, service, resource = message.key.decode("utf-8").split(" ")
            value = message.value.decode("utf-8")

            data_base.insert_metric(image_ID, service, resource, value)

            # get the expected usage given our model
            # in the future, we need a way to automatically get the service group for the current task and the run_time
            serviceID = data_base.get_ID_from_name(0, service)
            resourceID = data_base.get_ID_from_name(1, resource)
            inputs = [20, 10, 30] + [serviceID] + [resourceID] + [run_time]
            inputs = torch.tensor(inputs, dtype=torch.float32)
            prediction = model(inputs).data
            prediction = np.asarray(prediction)[0]

            # visualize the actual and the predicted resource usage for this service-resource pair
            plot_real.update(resource, float(value))
            plot_predicted.update(resource, prediction)

            # consume earliest available messages, don't commit offsets
            KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)
            # stopIteration if no message after 1sec
            KafkaConsumer(consumer_timeout_ms=1000)
    except KeyboardInterrupt:
        print("Stopped reading data")
        data_base.close_connection()

if __name__ == '__main__':
    main()