import os
import sys
import json
import time
import producer
from kafka import KafkaConsumer

TASK_NAME = "service2"
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer(TASK_NAME, bootstrap_servers=kafka_bootstrap_servers)
system_monitor_producer = producer.Producer("system", kafka_bootstrap_servers)
resource_monitor_producer = producer.Producer("resource", kafka_bootstrap_servers)
orchestrator_producer = producer.Producer("orchestrator", kafka_bootstrap_servers)

def do_computation(input):
    input *= 2
    time.sleep(3)

# listen to the orchestrators to know if the task needs to be applied to something
for message in consumer:
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