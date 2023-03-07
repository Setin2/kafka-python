
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, draw, show, ion
from kafka import KafkaConsumer

class Plot():
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

def save_to_file(filename, data):
    with open('data/{fname}'.format(fname = filename), 'a') as f:
        f.write(data + "\n")

consumer = KafkaConsumer("resources", "my-group", bootstrap_servers=['localhost:9092'])
plot = Plot()

for message in consumer:
    key = message.key.decode("utf-8")
    value = message.value.decode("utf-8")
    
    plot.update(key, float(value))
    save_to_file(key, value)

    # consume earliest available messages, don't commit offsets
    KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)
    # StopIteration if no message after 1sec
    KafkaConsumer(consumer_timeout_ms=1000)