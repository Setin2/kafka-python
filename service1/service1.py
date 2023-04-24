import os
import sys
import json
import time
import producer

task_input = json.loads(sys.argv[1])

required_tasks = task_input["required_tasks"]
task_name = task_input["task_name"]
orderID = str(task_input["orderID"])
pid = os.getpid()

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
monitoring_producer = producer.Producer("task" + orderID, kafka_bootstrap_servers)
orchestrator_producer = producer.Producer("orchestrator", kafka_bootstrap_servers)

# task start, notify the monitoring producer
monitoring_producer.send("ORDER", str(required_tasks) + ":" + task_name + ":" + str(pid) + ":" + orderID)

# do the computation
task_input["input"] += 2
task_input["done"].append(task_name)

# task ended, notify the monitorin producer and the orchestrator
orchestrator_producer.send("PROGRESS", json.dumps(task_input))
monitoring_producer.send("HALT", "HALT")

# order finished, notify the monitoring producer
if task_name in required_tasks[len(required_tasks) - 1]:
    monitoring_producer.send("STOP", "STOP")