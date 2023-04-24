import os
import sys
import json
import time
import psutil
import producer
import datetime
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
orderID = sys.argv[1]
producer = producer.Producer("system" + orderID, kafka_bootstrap_servers)
consumer = KafkaConsumer("system", bootstrap_servers=kafka_bootstrap_servers)

TASK_INSTANCE_TRESHOLD = 5 # basically how many orders can one instance of a task handle
ACTIVE_ORDERS = 0
ACTIVE_TASKS = 0
UPCOMING_ORDERS = []

def handle_idle_task(task_name):
    print("task idle")
    # check every X seconds if task is still idle, if yes, then close it
    # also check if the task is seen anywhere in the next few orders

def handle_upcoming_orders():
    for order in UPCOMING_ORDERS:
        # 
        print(order)

def handle_active_orders(message):
    orders, value = message.split(":")
    orders = eval(orders)
    ACTIVE_ORDERS += value
    UPCOMING_ORDERS.append(orders)
    handle_upcoming_orders()

def handle_active_tasks(message):
    task, value = message.split(":")
    ACTIVE_TASKS += value
    task_instances[task] += value
    # this task is now idle
    if task_instances[task] == 0:
        handle_idle_task()
    # check if we have many upcoming orders that require the task to be completed
    upcoming_orders_with_given_task = 0
    for order in orders:
        if task in order: upcoming_orders_with_given_task += 1
    if upcoming_orders_with_given_task / task_instances[task] > TASK_INSTANCE_TRESHOLD:
        print("start a new instance for this task")

key_to_method = {
    "ACTIVE_ORDERS": handle_active_orders,
    "ACTIVE_TASKS": handle_active_tasks
}

task_instances = {
    "service1": 0,
    "service2": 0,
    "service3": 0
}

task_idle_time = {
    "service1": 0,
    "service2": 0,
    "service3": 0
}

while True:
    try:
        # check to see if we got a new message
        new_message = consumer.poll(100)

        # if so, we get the message output of the task
        if new_message:
            # we need to loop thorugh the partition message
            for tp, messages in new_message.items():
                for message in messages:
                    key = message.key.decode("utf-8")
                    message = message.value.decode("utf-8")
                    key_to_method[key](message)
                    key_to_method[key](message)
    except KafkaError as e:
        print(f'Error: {e}', flush=True)