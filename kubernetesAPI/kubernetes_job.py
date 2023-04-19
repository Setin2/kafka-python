import json
import uuid
import time
from kubernetesAPI import variables
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

# Dont know, some things we need to do stuff
config.load_kube_config()

namespace = variables.NAMESPACE
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_job(service_name, args=[]):
    """
        Create a kubernetes job with for a given service

        Args:
            service_name (str): name of the service that was tagged and pushed to a continer repository (like docker hub)
            args ([str]): list of arguments to give to the service container (if any are needed)
        
        Returns:
            kubernetes.client.BatchV1Api.V1Job: the kubernetes job
    """
    # Define the YAML for the job
    job = client.V1Job()
    job.api_version = "batch/v1"
    job.kind = "Job"
    job.metadata = client.V1ObjectMeta(name=service_name + "-" + args[0])
    job.spec = client.V1JobSpec(
        completions=1,
        ttl_seconds_after_finished=1,  # Automatically delete the job after 1 second
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": service_name}),
            spec=client.V1PodSpec(
                restart_policy="Never",
                host_network=False,
                service_account_name="orchestrator",
                containers=[
                    client.V1Container(
                        name=service_name,
                        image=f"{variables.DOCKER_HUB_NAME}/{service_name}:latest",
                        command=["python", f"{service_name}.py"] + args,
                        ports=[client.V1ContainerPort(name="kafka-python", container_port=9092)],
                        env=[
                            client.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value=variables.KAFKA_BOOTSTRAP_SERVERS),
                            client.V1EnvVar(name="KAFKA_ZOOKEEPER_CONNECT", value=variables.KAFKA_ZOOKEEPER_CONNECT),
                            client.V1EnvVar(name="POSTGRES_HOST", value=variables.POSTGRES_HOST),
                            client.V1EnvVar(name="POSTGRES_NAME", value=variables.POSTGRES_NAME),
                            client.V1EnvVar(name="POSTGRES_USER", value=variables.POSTGRES_USER),
                            client.V1EnvVar(name="POSTGRES_PASSWORD", value=variables.POSTGRES_PASSWORD)
                        ]
                    )
                ]
            )
        )
    )

    # Create the Job
    return batch_v1.create_namespaced_job(namespace=namespace, body=job)

def wait_for_job_completion(service_name):
    """
        Read the events for a service with the given name and wait for a success or failure event.

        Args:
            service_name (str): name of the service whose events we want to read
    """
    while True:
        try:
            job_status = batch_v1.read_namespaced_job_status(name=service_name, namespace=namespace)
            if job_status.status.succeeded:
                print(f"Job {service_name} finished successfully.")
                return
            elif job_status.status.failed:
                raise Exception("Job failed")
        except ApiException as e:
            if e.status == 404:
                # Job not found yet, continue waiting
                pass
            else:
                # Some other error occurred, raise it
                raise e
        time.sleep(1)  # Wait for 1 second before checking the job status again

def delete_pod_and_job(job_name):
    batch_v1.delete_namespaced_job(name=job_name, namespace=namespace, body=client.V1DeleteOptions(propagation_policy="Background"))
    # Delete the associated pods
    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=f"app={job_name}")
    for pod in pods.items:
        v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace, body=client.V1DeleteOptions(propagation_policy="Background", grace_period_seconds=0))
    print(f"Deleting {job_name}...")

# Delete the deployment with service
def delete_deployment_and_service(service, delete_deployment, delete_service):
    if delete_deployment:
        deployment_name = service
        api_instance = client.AppsV1Api()
        api_instance.delete_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=client.V1DeleteOptions(),
        )
    
    if delete_service:
        # Delete the service
        service_name = service
        api_instance = client.CoreV1Api()
        api_instance.delete_namespaced_service(
            name=service_name,
            namespace=namespace,
            body=client.V1DeleteOptions(),
        )