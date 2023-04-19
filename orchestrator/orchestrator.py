import os
import sys
import time
import producer
import kubernetes_job_cluster
from kafka import KafkaConsumer

orderID = sys.argv[1]
required_tasks = sys.argv[2]
required_tasks = eval(required_tasks)

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer("orchestrator", "services_group", bootstrap_servers=kafka_bootstrap_servers)
progress = ""

# start the required tasks in the order specified
for i, task_name in enumerate(required_tasks):
    # start the job for the task (the task will notify the monitoring job that a new task has started)
    task_job = kubernetes_job_cluster.create_job(task_name, [str(required_tasks), task_name, orderID, progress])
    task_done = False

    # listen to the consumer to see if the task is finished
    while not task_done:
        # check to see if we got a new message
        new_message = consumer.poll(0.1)
        
        # if so, we get the message output of the task
        if new_message:
            # we need to loop thorugh the partition message
            for tp, messages in new_message.items():
                for message in messages:
                    task_done = True
                    progress = message.value.decode("utf-8")
        time.sleep(1)

print(progress)
