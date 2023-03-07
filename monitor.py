
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, draw, show, ion
from kafka import KafkaConsumer

class Plot():
    def __init__(self):
        self.labels = ['Used', 'Available']
        self.fig1, self.ax1 = plt.subplots(1, 2)
        plt.ion()
        self.ax1[0].pie([50, 50], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        self.ax1[0].axis('equal')
        self.ax1[1].pie([50, 50], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        self.ax1[1].axis('equal')
        plt.pause(0.001)
        plt.show()

    def update(self, val, resource):
        if resource == "CPU":
            self.ax1[0].clear()
            self.ax1[0].pie([val, 100-val], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        elif resource == "RAM":
            self.ax1[1].clear()
            self.ax1[1].pie([val, 100-val], explode=(0.1, 0), labels=self.labels, autopct='%1.1f%%', startangle=90)
        # re-drawing the figure
        self.fig1.canvas.draw()
        # to flush the GUI events
        self.fig1.canvas.flush_events()

consumer = KafkaConsumer("my-topic", "my-group", bootstrap_servers=['localhost:9092'])
plot = Plot()

for message in consumer:
    key = message.key.decode("utf-8")
    value = message.value.decode("utf-8")
    
    #plot.update(float(value), key)
    plot.update(float(value), key)

    # consume earliest available messages, don't commit offsets
    KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)
    # StopIteration if no message after 1sec
    KafkaConsumer(consumer_timeout_ms=1000)