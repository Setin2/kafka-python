from kubernetes import client, config, watch
import json
import time

config.load_kube_config()

namespace = "kafka-python"
#namespace.metadata = client.V1ObjectMeta(name="kafka-python")

v1 = client.CoreV1Api()
#v1.create_namespace(namespace)
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_job(service_name, args=[]):
    # Define the YAML for the job
    job = client.V1Job()
    job.api_version = "batch/v1"
    job.kind = "Job"
    job.metadata = client.V1ObjectMeta(name=service_name)
    job.spec = client.V1JobSpec(
        completions=1,
        ttl_seconds_after_finished=1,  # Automatically delete the job after 1 second
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": service_name}),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[
                    client.V1Container(
                        name=service_name,
                        image=f"setin/{service_name}:latest",
                        command=["python", f"{service_name}.py"] + args,
                        env=[
                            client.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value="broker:9092"),
                            client.V1EnvVar(name="KAFKA_ZOOKEEPER_CONNECT", value="zookeeper:2181"),
                            client.V1EnvVar(name="POSTGRES_HOST", value="db:5432"),
                            client.V1EnvVar(name="POSTGRES_USER", value="postgres"),
                            client.V1EnvVar(name="POSTGRES_PASSWORD", value="postgres"),
                            client.V1EnvVar(name="POSTGRES_DB", value="mydatabase"),
                            client.V1EnvVar(name="SECRET_KEY", value="my-secret-key")  # add your environment variable here
                        ]
                    )
                ]
            )
        )
    )

    # Create the Job
    return batch_v1.create_namespaced_job(namespace=namespace, body=job)

#kubectl apply -f Namespace.YAML    
#docker-compose --project-name my-project --network kafka-python up -d
#docker run --network=kafka-python_default monitor-producer
#kafka-python_default

def wait_for_job_completion(service_name):
    print(f"Waiting for {service_name} to complete...")
    w = watch.Watch()
    # timeout_seconds=0 -> will run watch for infinite time, but doesn't raise exception when wait is over
    # _request_timeout=timeout -> it is max timeout for request
    for event in w.stream(
        batch_v1.list_namespaced_job,
        namespace=namespace,
        label_selector=f"job-name={service_name}",
        timeout_seconds=0
    ):
        o = event["object"]

        if o.status.succeeded:
            print("Job succses")
            w.stop()
            return

        if not o.status.active and o.status.failed:
            w.stop()
            raise Exception("Job Failed")
    batch_v1.delete_namespaced_job(name="monitor-producer", namespace=namespace, body=client.V1DeleteOptions())

# Read the tasks JSON file
with open("order.json", "r") as tasks_file:
    tasks = json.load(tasks_file)

# Start the required services
for service_name in tasks["required_services"]:
    #batch_v1.delete_namespaced_job(name=f"{service_name}", namespace="default", body=client.V1DeleteOptions())
    service_job = create_job(service_name)
    print("started service" + service_name)
    monitor_job = create_job("monitor-producer", [service_name, tasks["taskID"]])
    print("started monitor producer")
    wait_for_job_completion(service_name)

"""
docker build -t service1:latest service1
docker tag service1:latest setin/service1:latest
docker push setin/service1:latest
"""