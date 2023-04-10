from kubernetes import client, config, watch
import json
import time

# Dont know, some things we need to do stuff
config.load_kube_config()
namespace = "default"
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_zookeeper(start_deployment=True, start_service=True):
    # define and start a kafka zookeeper deployment
    if start_deployment:
        zookeeper_deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name="zookeeper"),
            spec=client.V1DeploymentSpec(
                selector=client.V1LabelSelector(match_labels={"app": "zookeeper"}),
                replicas=1,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": "zookeeper"}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="zookeeper",
                                image="confluentinc/cp-zookeeper:7.3.0",
                                env=[
                                    client.V1EnvVar(name="ZOOKEEPER_CLIENT_PORT", value="2181"),
                                    client.V1EnvVar(name="ZOOKEEPER_TICK_TIME", value="2000")
                                ],
                                ports=[client.V1ContainerPort(container_port=2181)]
                            )
                        ]
                    )
                )
            )
        )
        apps_v1.create_namespaced_deployment(body=zookeeper_deployment, namespace="default")

    if start_service:
        # define and start a kafka zookeeper service
        zookeeper_service = client.V1Service(
            metadata=client.V1ObjectMeta(name="zookeeper"),
            spec=client.V1ServiceSpec(
                selector={"app": "zookeeper"},
                ports=[client.V1ServicePort(port=2181)]
            )
        )
        v1.create_namespaced_service(body=zookeeper_service, namespace="default")