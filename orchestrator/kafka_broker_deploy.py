from kubernetes import client, config, watch
import json
import time

# Dont know, some things we need to do stuff
config.load_kube_config()
namespace = "default"
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
                "name": "kafka-broker"
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": "kafka-broker"
                    }
                },
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "kafka-broker"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "kafka-broker",
                                "image": "confluentinc/cp-kafka:7.3.0",
                                "env": [
                                    {"name": "KAFKA_BROKER_ID","value": "1"},
                                    {"name": "KAFKA_ZOOKEEPER_CONNECT","value": "zookeeper:2181"},
                                    {"name": "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP", "value": "PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT"},
                                    {"name": "KAFKA_ADVERTISED_LISTENERS", "value": "PLAINTEXT://localhost:29092,PLAINTEXT_INTERNAL://kafka-broker:9092" },
                                    {"name": "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR", "value": "1" },
                                    {"name": "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR", "value": "1" },
                                    { "name": "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR", "value": "1" }
                                ],
                                "ports": [
                                    {"name": "kafka", "containerPort": 9092 },
                                    {"name": "kafka-internal", "containerPort": 9092 } #29092
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
                                    { "name": "kafka-storage", "mountPath": "/var/lib/kafka/data" }
                                ]
                            }
                        ],
                        "volumes": [
                            { "name": "kafka-storage", "emptyDir": {}}
                        ]
                    }
                }
            }
        }
        apps_v1.create_namespaced_deployment(body=broker_deployment, namespace="default" )

    if start_service:
        # define and start a kafka broker service
        # this is a LoadBalancer service since we need to communicate with it externally
        broker_service = client.V1Service(
            metadata=client.V1ObjectMeta(name="kafka-broker"),
            spec=client.V1ServiceSpec(
                selector={"app": "kafka-broker"},
                type="LoadBalancer",
                ports=[client.V1ServicePort(port=9092)]
            )
        )
        v1.create_namespaced_service(body=broker_service, namespace="default")