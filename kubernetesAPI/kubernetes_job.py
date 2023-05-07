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

def create_service_and_deployment(service_name, start_deployment=True, start_service=True, service_type=1, replicas=1, args=[]):
    """
    Create a kubernetes service and deployment for a given service

    Args:
        service_name (str): name of the service that was tagged and pushed to a container repository (like docker hub)
        service_type (int): 1 for LoadBalancer, 2 for NodePort (used by the proxy server since it needs to communicate via HTTP requests)
        replicas (int): number of replicas for the deployment (default 1)
        args ([str]): list of arguments to give to the service container (if any are needed)
    """
    if start_deployment:
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

    if service_type == 1:
        service_type = "LoadBalancer" 
    elif service_type == 2 : service_type = "NodePort"

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