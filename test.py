import os
import sys
import json
import time
import psutil
import datetime

"""kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
orderID = sys.argv[1]
producer = producer.Producer("system" + orderID, kafka_bootstrap_servers)
consumer = KafkaConsumer("system", bootstrap_servers=kafka_bootstrap_servers)
"""

TASK_INSTANCE_TRESHOLD = 8 # how many orders can one instance of a task handle at most
ACTIVE_ORDERS = 0
ACTIVE_TASKS = 0
ACTIVE_INSTANCES = 0
UPCOMING_ORDERS = []

def handle_idle_task(task_name):
    print("task idle")
    # check every X seconds if task is still idle, if yes, then close it
    # also check if the task is seen anywhere in the next few orders

def handle_upcoming_orders():
    global UPCOMING_ORDERS
    for order in UPCOMING_ORDERS:
        # 
        #print(order)
        pass

def handle_active_orders(message):
    global ACTIVE_ORDERS
    global UPCOMING_ORDERS
    order, value = message.split(":")
    order, value = eval(order), int(value)
    # order just started
    if value == 1:
        ACTIVE_ORDERS += 1
        print(f"ACTIVE_ORDERS went to {ACTIVE_ORDERS}")
        UPCOMING_ORDERS.append(order)
        print(f"UPCOMING_ORDERS went to {UPCOMING_ORDERS}")
    # order is done, remove it form UPCOMING_ORDERS
    else:
        ACTIVE_ORDERS -= 1
        print(f"ACTIVE_ORDERS went to {ACTIVE_ORDERS}")
        UPCOMING_ORDERS.remove(order)
        print(f"UPCOMING_ORDERS went to {UPCOMING_ORDERS}")
    handle_upcoming_orders()

def handle_active_tasks(message):
    global ACTIVE_TASKS
    global TASK_INSTANCE_TRESHOLD
    global UPCOMING_ORDERS
    task, value = message.split(":")
    value = int(value)
    ACTIVE_TASKS += value
    print(f"ACTIVE_TASKS went to {ACTIVE_TASKS}")
    running_tasks[task] += value
    print(f"number of orders with {task} is {running_tasks[task]}")
    # this task is now idle
    if running_tasks[task] == 0:
        handle_idle_task(task)
    # check if we have many upcoming orders that require the task to be completed
    upcoming_orders_with_given_task = 0
    for order in UPCOMING_ORDERS:
        if task in order: upcoming_orders_with_given_task += 1
    # if the number of orders per task is bigger than the treshold, start a new instance of the task
    if upcoming_orders_with_given_task / task_instances[task] > TASK_INSTANCE_TRESHOLD:
        if not upcoming_orders_with_given_task / (task_instances[task] + 1) < (task_instances[task] + 1):
            print(f"start a new instance for this task {upcoming_orders_with_given_task}")
    # if the number of orders per task is smaller than number of instances, we delete an instance
    elif upcoming_orders_with_given_task / task_instances[task] < task_instances[task]:
        print(f"delete an instance for this task {upcoming_orders_with_given_task}") 

def handle_active_instances(message):
    global ACTIVE_INSTANCES
    task, value = message.split(":")
    value = int(value)
    ACTIVE_INSTANCES += value
    print(f"ACTIVE_INSTANCES went to {ACTIVE_INSTANCES}")
    task_instances[task] += value
    print(f"number of instances of {task} is {task_instances[task]}")

# ACTIVE_ORDERS<["service1"]:1
# ACTIVE_TASKS<service1:1
# ACTIVE_INSTANCES<service1:1

key_to_method = {
    "ACTIVE_ORDERS": handle_active_orders,
    "ACTIVE_TASKS": handle_active_tasks,
    "ACTIVE_INSTANCES": handle_active_instances
}

running_tasks = {
    "service1": 0,
    "service2": 0,
    "service3": 0
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
    # check to see if we got a new message
    new_message = input()
    key, value = new_message.split("<")
    key_to_method[key](value)
