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

def create_broker(start_deployment=True, start_service=True):
    if start_deployment:
        # define and start a kafka broker deployment
        broker_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": variables.BROKER_NAME
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": variables.BROKER_NAME
                    }
                },
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": variables.BROKER_NAME
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": variables.BROKER_NAME,
                                "image": variables.BROKER_IMAGE,
                                "env": [
                                    {"name": "KAFKA_BROKER_ID","value": "1"},
                                    {"name": "KAFKA_ZOOKEEPER_CONNECT","value": variables.KAFKA_ZOOKEEPER_CONNECT},
                                    {"name": "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP", "value": variables.KAFKA_LISTENER_SECURITY_PROTOCOL_MAP},
                                    {"name": "KAFKA_ADVERTISED_LISTENERS", "value": variables.KAFKA_ADVERTISED_LISTENERS },
                                    {"name": "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR", "value": variables.KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR },
                                    {"name": "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR", "value": variables.KAFKA_TRANSACTION_STATE_LOG_MIN_ISR },
                                    { "name": "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR", "value": variables.KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR }
                                ],
                                "ports": [
                                    {"name": "kafka", "containerPort": variables.BROKER_PORT },
                                    {"name": "kafka-internal", "containerPort": variables.BROKER_PORT } #29092
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "256Mi"
                                    },
                                    "limits": {
                                        "cpu": "500m",
                                        "memory": "1Gi"
                                    }
                                },
                                "volumeMounts": [
                                    { "name": variables.BROKER_VOLUME_NAME, "mountPath": variables.BROKER_VOLUME_MOUNT_PATH }
                                ]
                            }
                        ],
                        "volumes": [
                            { "name": variables.BROKER_VOLUME_NAME, "emptyDir": {}}
                        ]
                    }
                }
            }
        }
        apps_v1.create_namespaced_deployment(body=broker_deployment, namespace=namespace)

    if start_service:
        # define and start a kafka broker service
        # this is a LoadBalancer service since we need to communicate with it externally
        broker_service = client.V1Service(
            metadata=client.V1ObjectMeta(name=variables.BROKER_NAME),
            spec=client.V1ServiceSpec(
                selector={"app": variables.BROKER_NAME},
                type="LoadBalancer",
                ports=[client.V1ServicePort(port=variables.BROKER_PORT)]
            )
        )
        v1.create_namespaced_service(body=broker_service, namespace=namespace)