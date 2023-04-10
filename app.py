import json
import time
from misc import producer
from kafka import KafkaProducer
from orchestrator import kubernetes_job
from orchestrator import database_deploy
from orchestrator import kafka_broker_deploy
from orchestrator import kafka_zookeeper_deploy

#kafka_zookeeper_deploy.create_zookeeper(start_deployment=True, start_service=False)
#kafka_broker_deploy.create_broker(start_deployment=True, start_service=False)
#database_deploy.create_database(start_deployment=True, start_service=False)

# Read the file with the given order
with open("order.json", "r") as tasks_file:
    tasks = json.load(tasks_file)

# extract the order and send it to the orchestrator job
required_services = str(tasks["required_services"])
taskID = tasks["taskID"]
orchestrator_job = kubernetes_job.create_job("orchestrator", [taskID, required_services])
kubernetes_job.wait_for_job_completion("orchestrator")

# start monitoring
#monitor_consumer_job = kubernetes_job.create_job("monitor-consumer")
#monitor_producer_job = kubernetes_job.create_job("monitor-producer")

# python kubernetes_orc.py
#kubernetes_job.delete_pod_and_job("monitor-producer")
#kubernetes_job.delete_pod_and_job("monitor-consumer")