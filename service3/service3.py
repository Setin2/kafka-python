import os
import time
import sys
import producer

required_tasks = sys.argv[1]
required_tasks = eval(required_tasks)
task_name = sys.argv[2]
orderID = sys.argv[3]
progress = sys.argv[4]

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
monitoring_producer = producer.Producer("task" + orderID, kafka_bootstrap_servers)
orchestrator_producer = producer.Producer("orchestrator", kafka_bootstrap_servers)

# task start, notify the monitoring producer
monitoring_producer.send("ORDER", str(required_tasks) + ":" + task_name + ":" + orderID)

time.sleep(4)

output = "Hello from service 3"

# task ended, notify the monitorin producer and the orchestrator
orchestrator_producer.send("PROGRESS", progress + ":" + output)
monitoring_producer.send("HALT", "HALT")

# order finished, notify the monitoring producer
if task_name in required_tasks[len(required_tasks) - 1]:
    monitoring_producer.send("STOP", "STOP")