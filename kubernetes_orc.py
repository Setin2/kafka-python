from kubernetes import client, config
import json
import time

config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_deployment(service_name):
    # Define the YAML for the deployment
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
                        image=f"{service_name}:latest"#,
                        #command=command,
                    )
                ]
            )
        )
    )

    # Create the Job
    batch_v1.create_namespaced_job(namespace="default", body=job)


"""
    For starting a monitoring service for each service
"""
def create_job(service_name, task_ID):
    # Define the monitoring Job
    job = client.V1Job(
        metadata=client.V1ObjectMeta(name=f"{service_name}-monitor-producer"),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": f"{service_name}-monitor-producer"}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="monitor-producer",
                            image="busybox",
                            command=[
                                "python",
                                "monitor.py",
                                service_name,
                                tast_ID
                            ]
                        )
                    ],
                    restart_policy="Never"
                )
            ),
            backoff_limit=0
        )
    )
    # Create the monitoring Job
    batch_v1.create_namespaced_job(namespace="default", body=job)

    # Wait for service_name to complete
    deployment = apps_v1.read_namespaced_deployment_status(name=service_name, namespace="default")
    while deployment.status.ready_replicas != deployment.status.replicas:
        deployment = apps_v1.read_namespaced_deployment_status(name=service_name, namespace="default")
        time.sleep(1)

    # Delete the monitoring Job
    api.delete_namespaced_job(name=f"{service_name}-monitor", namespace="default", body=client.V1DeleteOptions())


#api_instance = client.BatchV1Api()
#api_instance.delete_namespaced_job(name="service2", namespace="default")
#api_instance.delete_namespaced_job(name="service3", namespace="default")

# Read the tasks JSON file
with open("order.json", "r") as tasks_file:
    tasks = json.load(tasks_file)

# Start the required services
for service_name in tasks["required_services"]:
    # Create the Deployment
    create_deployment(service_name)
    print(service_name, " done")

    # Create the CronJob
    #create_cronjob(service_name)