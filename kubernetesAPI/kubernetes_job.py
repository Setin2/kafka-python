import os
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
                service_account_name=variables.SERVICE_ACCOUNT_NAME,
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

def create_service_and_deployment(service_name, start_service=0, replicas=1, args=[]):
    """
    Create a kubernetes service and deployment for a given service

    Args:
        service_name (str): name of the service that was tagged and pushed to a container repository (like docker hub)
        replicas (int): number of replicas for the deployment (default 1)
        args ([str]): list of arguments to give to the service container (if any are needed)

    Returns:
        Tuple[kubernetes.client.AppsV1Api.V1Deployment, kubernetes.client.CoreV1Api.V1Service]: the kubernetes deployment and service
    """
    # Define the YAML for the deployment
    deployment = client.V1Deployment()
    deployment.api_version = "apps/v1"
    deployment.kind = "Deployment"
    deployment.metadata = client.V1ObjectMeta(name=service_name)
    deployment.spec = client.V1DeploymentSpec(
        replicas=replicas,
        selector=client.V1LabelSelector(match_labels={"app": service_name}),
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": service_name}),
            spec=client.V1PodSpec(
                service_account_name=variables.SERVICE_ACCOUNT_NAME,
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

    # Create the deployment
    deployment = apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)

    if start_service == 1:
        service_type = "LoadBalancer" 
    elif start_service == 2 : service_type = "NodePort"

    if start_service:
        # Define the YAML for the service
        service = client.V1Service()
        service.api_version = "v1"
        service.kind = "Service"
        service.metadata = client.V1ObjectMeta(name=service_name)
        service.spec = client.V1ServiceSpec(
            selector={"app": service_name},
            ports=[client.V1ServicePort(port=80, target_port=9092)],
            type=service_type
        )

        # Create the service
        service = v1.create_namespaced_service(namespace=namespace, body=service)

def scale_deployment(deployment_name, replicas):
    api = client.AppsV1Api()
    try:
        deployment = api.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        deployment.spec.replicas = replicas
        api.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)
        print(f"Deployment {deployment_name} scaled to {replicas} replicas")
    except ApiException as e:
        print(f"Exception when calling AppsV1Api->patch_namespaced_deployment: {e}\n")

def get_deployment_replicas(deployment_name):
    api = client.AppsV1Api()
    try:
        deployment = api.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        return deployment.spec.replicas
    except ApiException as e:
        print(f"Exception when calling AppsV1Api->read_namespaced_deployment: {e}\n")

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