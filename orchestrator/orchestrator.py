import os
import sys
import time
import json
import psutil
import producer
import datetime
import resource_consumption
import kubernetes_job_cluster
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from kafka.admin import KafkaAdminClient, NewPartitions
from kafka import KafkaAdminClient, KafkaConsumer
from kafka import TopicPartition

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer("orchestrator", bootstrap_servers=kafka_bootstrap_servers)
monitor_producer = producer.Producer("system", kafka_bootstrap_servers)

#admin_client = KafkaAdminClient(bootstrap_servers=kafka_bootstrap_servers)
#admin_client.create_partitions({"service1": NewPartitions(4)})

orders = {}

def start_new_order(message):
    global monitor_producer
    global orders
    # get the order
    order = json.loads(message)
    orderID = order["orderID"]
    orders[orderID] = order
    required_tasks = order["required_tasks"]
    task_name = required_tasks[len(order["done"])]
    print(f"Starting order with ID {orderID}", flush=True)
    # notify the system monitor that a new order and the first task have started
    monitor_producer.send("ORDER", str(orderID) + ":" + json.dumps(required_tasks) + ":" + "1")
    # notify the first non-completed task in the order
    task_producer = producer.Producer(task_name, kafka_bootstrap_servers)
    task_producer.send(str(orderID), json.dumps(order))

def change_system(message):
    global monitor_producer
    task_name, value = message.split(":")
    # get the new number of instances for this task
    num_instances = kubernetes_job_cluster.get_deployment_replicas(task_name)
    new_num_instances = num_instances + int(value)
    # scale the instances depending on the provided value
    kubernetes_job_cluster.scale_deployment("service1", new_num_instances)
    #print(f"Change in system. New number of replicas for {task_name} is {new_num_instances}", flush=True)
    # notify the system monitor
    monitor_producer.send("INSTANCE", task_name + ":" + str(value))

def update_order(message):
    global monitor_producer
    global orders
    updated_order = json.loads(message)
    orderID = updated_order["orderID"]
    required_tasks = updated_order["required_tasks"]

    task_done = updated_order["done"][len(updated_order["done"]) - 1]
    # order is done, delete it from the list and notify the system monitor
    if len(updated_order["done"]) == len(required_tasks):
        print(f"Order with ID {orderID} is done", flush=True)
        if orderID in orders:
            del orders[orderID]
    # order is not done, notify the next service in line and the monitor producer
    else:
        task_name = required_tasks[len(updated_order["done"])]
        #print(f"Order with ID {orderID} continues with task {task_name}", flush=True)
        task_producer = producer.Producer(task_name, kafka_bootstrap_servers)
        task_producer.send("TASK", json.dumps(updated_order))

key_to_method = {
    "START": start_new_order,           # we got a new order       
    "SERVICE": change_system,            # a change in the system needs to occur
    "PROGRESS": update_order            # a task started or finished
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