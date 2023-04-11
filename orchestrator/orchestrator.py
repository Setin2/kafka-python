import os
import sys
import producer
import kubernetes_job_cluster

orderID = sys.argv[1]
required_tasks = sys.argv[2]
required_tasks = eval(required_tasks)

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
producer = producer.Producer("services", kafka_bootstrap_servers)

# start the required tasks in the order specified
for i, task_name in enumerate(required_tasks):
    # start the job for the task and notify the monitoring job that a new task has started
    task_job = kubernetes_job_cluster.create_job(task_name, [str(required_tasks), task_name, orderID])
    task_job = kubernetes_job_cluster.create_job(task_name, [str(required_tasks), task_name, orderID])
    producer.send(str(required_tasks) + ":" + task_name, orderID)
    # wait for the job to complete
    kubernetes_job_cluster.wait_for_job_completion(task_name)
    # if this is the last task in the order, 
    if task_name == required_tasks[len(required_tasks) - 1]:
        print(task_name, flush=True)
        producer.send("TERMINATE", "TERMINATE")

