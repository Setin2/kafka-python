import os
import sys
import time
import json
import psutil
import producer
import resource_consumption
import kubernetes_job_cluster
from kafka import KafkaConsumer
from kafka.errors import KafkaError

arguments = sys.argv[2]
orchestrator_input = json.loads(arguments)
required_tasks = orchestrator_input['required_tasks']
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
consumer = KafkaConsumer("orchestrator", bootstrap_servers=kafka_bootstrap_servers)

# first task input
task_input = {
    "input": orchestrator_input['input'],
    "orderID": orchestrator_input['orderID'],
    "required_tasks": required_tasks,
    "task_name": '',
    "done": orchestrator_input['done']
}

# start the required tasks in the order specified
for i, task_name in enumerate(required_tasks):
    # start the job for the task (the task will notify the monitoring job that a new task has started)
    task_input["task_name"] = task_name
    task_job = kubernetes_job_cluster.create_job(task_name, [json.dumps(task_input)])
    print(task_input, flush=True)

    # listen to the consumer to see if the task is finished
    task_done = False
    while not task_done:
        try:
            # check to see if we got a new message
            new_message = consumer.poll(0.1)
            
            # if so, we get the message output of the task
            if new_message:
                # we need to loop thorugh the partition message
                for tp, messages in new_message.items():
                    for message in messages:
                        task_done = True
                        task_input = json.loads(message.value.decode("utf-8"))
            time.sleep(1)
        except KafkaError as e:
            print(f'Error: {e}', flush=True)

print("done")
print(task_input)
