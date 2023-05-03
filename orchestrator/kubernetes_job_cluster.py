from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

# Dont know, some things we need to do stuff
config.load_incluster_config()

namespace = "default"
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

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