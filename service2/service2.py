import os
import sys
import json
import time
import producer
from kafka import KafkaConsumer

TASK_NAME = "service2"
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer(TASK_NAME, bootstrap_servers=kafka_bootstrap_servers)

# listen to the orchestrators to know if the task needs to be applied to something
for message in consumer:
    print("start", flush=True)
    # we got a message from the orchestrator
    task_input = json.loads(message.value.decode("utf-8"))
    required_tasks = task_input["required_tasks"]
    orderID = str(task_input["orderID"])
    pid = os.getpid()

    monitoring_producer = producer.Producer("task" + orderID, kafka_bootstrap_servers)
    orchestrator_producer = producer.Producer("orchestrator" + orderID, kafka_bootstrap_servers)

    # task start, notify the monitoring producer
    monitoring_producer.send("ORDER", str(required_tasks) + ":" + TASK_NAME + ":" + str(pid) + ":" + orderID)

    # do the computation
    task_input["input"] *= 2
    task_input["done"].append(TASK_NAME)

    print("task end", flush=True)

    # task ended, notify the monitoring producer and the orchestrator
    orchestrator_producer.send("PROGRESS", json.dumps(task_input))
    monitoring_producer.send("HALT", "HALT")

    # order finished, notify the monitoring producer
    if TASK_NAME in required_tasks[len(required_tasks) - 1]:
        monitoring_producer.send("STOP", "STOP")
    time.sleep(1)