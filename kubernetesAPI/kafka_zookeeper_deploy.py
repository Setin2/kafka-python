import json
import time
from kubernetesAPI import variables
from kubernetes import client, config, watch

# Dont know, some things we need to do stuff
config.load_kube_config()
namespace = variables.NAMESPACE
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_zookeeper(start_deployment=True, start_service=True):
    # define and start a kafka zookeeper deployment
    if start_deployment:
        zookeeper_deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=variables.ZOOKEEPER_NAME),
            spec=client.V1DeploymentSpec(
                selector=client.V1LabelSelector(match_labels={"app": variables.ZOOKEEPER_NAME}),
                replicas=1,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": variables.ZOOKEEPER_NAME}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=variables.ZOOKEEPER_NAME,
                                image=variables.ZOOKEEPER_IMAGE,
                                env=[
                                    client.V1EnvVar(name="ZOOKEEPER_CLIENT_PORT", value=variables.ZOOKEEPER_PORT),
                                    client.V1EnvVar(name="ZOOKEEPER_TICK_TIME", value=variables.ZOOKEEPER_TICK_TIME)
                                ],
                                ports=[client.V1ContainerPort(container_port=int(variables.ZOOKEEPER_PORT))]
                            )
                        ]
                    )
                )
            )
        )
        apps_v1.create_namespaced_deployment(body=zookeeper_deployment, namespace=namespace)

    if start_service:
        # define and start a kafka zookeeper service
        zookeeper_service = client.V1Service(
            metadata=client.V1ObjectMeta(name=variables.ZOOKEEPER_NAME),
            spec=client.V1ServiceSpec(
                selector={"app": variables.ZOOKEEPER_NAME},
                ports=[client.V1ServicePort(port=int(variables.ZOOKEEPER_PORT))]
            )
        )
        v1.create_namespaced_service(body=zookeeper_service, namespace=namespace)