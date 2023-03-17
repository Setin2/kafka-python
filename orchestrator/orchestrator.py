import json
import sys
import os
import subprocess
import psutil
import time
import sys
sys.path.append('../')
import producer
import datetime
from kafka import KafkaConsumer

# get the order
data = None
with open('./order.JSON') as file: 
    data = json.load(file) # its a dictionary, like data['taskID']

consumer = KafkaConsumer("orchestrator", "my-group", bootstrap_servers=['localhost:9092'])
producer = producer.Producer()

monitor_consumer = subprocess.Popen('python ./monitor.py')

# while we havent gone through all the services in the order
while len(data['required_services']) > len(data['completed_services']):
    # start the next service in line
    subprocess.Popen('python ./{service}/{service}.py'.format(service=data['required_services'][len(data['completed_services'])]))
    service_processed = False

    # start the monitoring the service resource consumption producer
    monitoring_service = subprocess.Popen('python ./producer/producer.py {service} {taskID}'.format(
            service=data['required_services'][len(data['completed_services'])],
            taskID=data['taskID']
    ))

    # listen to the service
    while not service_processed:
        # we got a message, the service is done
        for message in consumer:
            # we might want to read the message
            key = message.key.decode("utf-8")
            value = message.value.decode("utf-8")
            # we update the JSON data
            data['completed_services'].append(data['required_services'][len(data['completed_services'])])
            # we kill the montor for this service and go to the next one
            monitoring_service.kill()
            service_processed = True
            break

monitor_consumer.kill()