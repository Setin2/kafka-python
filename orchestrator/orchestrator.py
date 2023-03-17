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

consumer = KafkaConsumer("orchestrator", bootstrap_servers=['localhost:9092'])
producer = producer.Producer()

cur_idx = 0
# while we havent gone through all the services in the order
try:
    for service in data['required_services']:
        # start the monitoring the service resource consumption producer
        monitoring_service = subprocess.Popen('python ./monitor-producer/monitor-producer.py {service} {taskID}'.format(service=service, taskID=data['taskID']))

        # start the next service in line
        subprocess.Popen('python ./{service}/{service}.py'.format(service=service))
        service_processed = False

        # listen to the service
        while not service_processed:
            # we got a message, the service is done
            for message in consumer:
                # we might want to read the message
                key = message.key.decode("utf-8")
                value = message.value.decode("utf-8")
                # we update the JSON data
                monitoring_service.kill()
                data['completed_services'].append(service)
                cur_idx += 1
                # we kill the montor for this service and go to the next one
                service_processed = True
                break
    #monitor_consumer.kill()
except KeyboardInterrupt:
    if monitoring_service: monitoring_service.kill()