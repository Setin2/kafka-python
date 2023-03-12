
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, draw, show, ion
from kafka import KafkaConsumer
import psycopg2
import datetime

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


# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="postgres",
    user="postgres",
    password="postgres"
)
# Create a table to store the data
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS metrics (service varchar(255), resource varchar(255), value double precision, timestamp timestamp)")
consumer = KafkaConsumer("resources", "my-group", bootstrap_servers=['localhost:9092'])
plot = Plot()

# Insert data into the table
def insert_metric(service, resource, value):
    ts = datetime.datetime.utcnow().replace(microsecond=0)
    cursor.execute("INSERT INTO metrics (service, resource, value, timestamp) VALUES (%s, %s, %s, %s)", (service, resource, value, ts))
    conn.commit()

for message in consumer:
    service, resource = message.key.decode("utf-8").split(" ")
    value = message.value.decode("utf-8")

    insert_metric(service, resource, value)
    plot.update(resource, float(value))
    #save_to_file(resource, value)

    # consume earliest available messages, don't commit offsets
    KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)
    # StopIteration if no message after 1sec
    KafkaConsumer(consumer_timeout_ms=1000)

cursor.close()
conn.close()