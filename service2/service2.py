import os
import sys
import json
import time
import producer
from datetime import datetime
from kafka import KafkaConsumer
from kafka import TopicPartition

TASK_NAME = "service2"
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer(TASK_NAME, group_id="group", bootstrap_servers=kafka_bootstrap_servers, enable_auto_commit=True)
system_monitor_producer = producer.Producer("system", kafka_bootstrap_servers)
resource_monitor_producer = producer.Producer("resource", kafka_bootstrap_servers)
orchestrator_producer = producer.Producer("orchestrator", kafka_bootstrap_servers)

def do_computation(input):
    input *= 2
    time.sleep(5)

def process_message(message):
    # we got a message from the orchestrator
    task_input = json.loads(message.value.decode("utf-8"))
    required_tasks = task_input["required_tasks"]
    orderID = str(task_input["orderID"])
    pid = os.getpid()

    # task start, notify the monitoring services
    resource_monitor_producer.send("ORDER", str(required_tasks) + ":" + TASK_NAME + ":" + str(pid) + ":" + orderID)
    system_monitor_producer.send("TASK", orderID + ":" + TASK_NAME + ":" + "1")

    do_computation(task_input["input"])

    # task ended, notify the monitoring services and the orchestrator
    task_input["done"].append(TASK_NAME)
    orchestrator_producer.send("PROGRESS", json.dumps(task_input))
    resource_monitor_producer.send("HALT", "HALT")

    # order finished, notify the monitoring service
    if TASK_NAME in required_tasks[len(required_tasks) - 1]:
        system_monitor_producer.send("ORDER", orderID + ":" + json.dumps(required_tasks) + ":" + "0")

    system_monitor_producer.send("TASK", orderID + ":" + TASK_NAME + ":" + "-1")

    time.sleep(1)

# listen to the orchestrators to know if the task needs to be applied to something
while True:
    try:
        # check to see if we got a new message
        new_message = consumer.poll(100)

        # if so, we get the message output of the task
        if new_message:
            # we need to loop thorugh the partition message
            for tp, messages in new_message.items():
                for message in messages:
                    print("GOT MESSAGE", flush=True)
                    process_message(message)
    except KafkaError as e:
        print(f'Error: {e}', flush=True)