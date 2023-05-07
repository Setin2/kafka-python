import os
import sys
import json
import time
import producer
import datetime
import threading
from kafka import KafkaProducer
from kafka import KafkaConsumer
from kafka.errors import KafkaError

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
producer = producer.Producer("orchestrator", kafka_bootstrap_servers)
consumer = KafkaConsumer("system", bootstrap_servers=kafka_bootstrap_servers)

IDLE_TIME_LIMIT = 3600      # how many seconds can a service stay idle for (one hour for now)
TASK_INSTANCE_TRESHOLD = 5  # how many orders can one instance of a task handle at most
NUM_ORDERS = 0              # number of orders started and not yet finished
NUM_TASKS = 0               # number of tasks currently doing some computation
NUM_UPCOMING_TASKS = 0      # number of tasks still yet to be performed
NUM_INSTANCES = 0           # sum of all instances of each task
ACTIVE_ORDERS = {}          # a dictionary of all the orderID and order pairs that have been started

last_message_time = {}      # dictionary to keep track of the last time each task was active
idle_check_threads = {}     # dictionary to keep track of idle check threads for each task

running_tasks = {           # dictionary to keep track of how many instances of each task are doing some computation
    "service1": 0,
    "service2": 0,
    "service3": 0
}

task_instances = {          # dictionary to keep track of how many instances of each task exist
    "service1": 1,
    "service2": 1,
    "service3": 1
}

def handle_idle_task(task_name):
    global last_message_time
    # check if the task is seen anywhere in the next few orders, we dont want to switch it off then
    for order in ACTIVE_ORDERS.values():
        if task_name in order:
            return
    # otherwise, start a thread that checks every X seconds if task is still idle, if after a certain amouunt of time it is still idle, we close it
    stop_flag = threading.Event()  # create a stop flag for the thread
    idle_check_thread = threading.Thread(target=check_idle_time, args=(task_name, stop_flag), daemon=True)
    idle_check_thread.start()
    idle_check_threads[task_name] = (idle_check_thread, stop_flag)

def check_idle_time(task, stop_flag):
    while not stop_flag.is_set():
        current_time = time.time()
        # if the idle time limit is exceeded, send a message to the orchestrator to switch off the service
        if current_time - last_message_time[task] > IDLE_TIME_LIMIT:
            producer.send("SERVICE", task + ":" + "-1")
            stop_flag.set()
            if task in idle_check_threads:
                del idle_check_threads[task]
            break
        time.sleep(60)  # wait for one minute before checking again

def update_active_orders(message):
    global NUM_ORDERS
    global ACTIVE_ORDERS
    global NUM_UPCOMING_TASKS
    orderID, order, value = message.split(":")
    order, value = json.loads(order), int(value)
    # order just started, add it to list of orders
    if value == 1:
        NUM_ORDERS += 1
        ACTIVE_ORDERS[orderID] = order
        #print(f"Changed list of active orders {ACTIVE_ORDERS}")
        NUM_UPCOMING_TASKS += len(order)
        # are there any thraeds checking if these tasks are idle
        for task, (thread, stop_flag) in list(idle_check_threads.items()):
            if task in order:
                # there are, set the stop flag and join the thread
                stop_flag.set()
                #thread.join()
                if task in idle_check_threads:
                    del idle_check_threads[task]
    # order is done, remove it from list of orders
    else:
        NUM_ORDERS -= 1
        if orderID in ACTIVE_ORDERS:
            del ACTIVE_ORDERS[orderID]

def update_active_tasks(message):
    global NUM_TASKS
    global TASK_INSTANCE_TRESHOLD
    global ACTIVE_ORDERS
    global NUM_UPCOMING_TASKS
    orderID, task, value = message.split(":")
    value = int(value)
    # we started a new task
    if value > 0:
        last_message_time[task] = time.time()
    # the task ended
    elif value < 0:
        NUM_UPCOMING_TASKS -= value
        last_message_time[task] = time.time()
    NUM_TASKS += value
    if task in running_tasks:
        running_tasks[task] += value
    # check how many started orders require the task to be completed
    upcoming_orders_with_given_task = 0
    for order in ACTIVE_ORDERS.values():
        if task in order: upcoming_orders_with_given_task += order.count(task)
    print(f"Active orders for this task is: {upcoming_orders_with_given_task}", flush=True)
    # the number of orders per task is bigger than the treshold (add 1 to avoid division by zero)
    # send a message to the orchestrator to start a new instance of the task
    if task in task_instances and task_instances[task] > 0 and (upcoming_orders_with_given_task+1)/(task_instances[task]+1) > TASK_INSTANCE_TRESHOLD:
        print("new instance", flush=True)
        #producer.send("SERVICE", task + ":" + "1")
    # we have more than 1 instance of this task, and the number of instances per orders is smaller than another threshold
    # send a message to to stop an instance of the task
    elif task in task_instances and task_instances[task] > 1 and upcoming_orders_with_given_task / task_instances[task] < TASK_INSTANCE_TRESHOLD - 0.5:
        print("less instance", flush=True)
        #producer.send("SERVICE", task + ":" + "-1")
    # this task is now idle
    if task not in running_tasks or running_tasks[task] == 0:
        handle_idle_task(task)

def update_active_instances(message):
    global NUM_INSTANCES
    task, value = message.split(":")
    value = int(value)
    NUM_INSTANCES += value
    task_instances[task] += value

key_to_method = {
    "ORDER": update_active_orders,          # message_value = orderID, order, value (value = 1 for starting an order, 0 for ending it)
    "TASK": update_active_tasks,            # message_value = orderID, task_name, value (value = by how much the num of tasks changed, must be non-zero)
    "INSTANCE": update_active_instances     # message_value = service_name, value (value = by how much the num of instances changed, must be non-zero)
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
                    value = message.value.decode("utf-8")
                    key_to_method[key](value)
    except KafkaError as e:
        print(f'Error: {e}', flush=True)