from kubernetes import client, config, watch
import json
import time

# Dont know, some things we need to do stuff
config.load_kube_config()
namespace = "default"
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_database(start_deployment=True, start_service=True):
    # define and start a database deployment
    if start_deployment:
        database_deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name="database"),
            spec=client.V1DeploymentSpec(
                selector=client.V1LabelSelector(match_labels={"app": "database"}),
                replicas=1,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": "database"}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="database",
                                image="postgres:14.1-alpine",
                                env=[
                                    client.V1EnvVar(name="POSTGRES_USER", value="postgres"),
                                    client.V1EnvVar(name="POSTGRES_PASSWORD", value="postgres")
                                ],
                                ports=[client.V1ContainerPort(container_port=5432)],
                                volume_mounts=[client.V1VolumeMount(name="database-volume", mount_path="/var/lib/postgresql/data")]
                            )
                        ],
                        volumes=[client.V1Volume(name="database-volume", empty_dir={})]
                    )
                )
            )
        )
        apps_v1.create_namespaced_deployment(body=database_deployment, namespace="default")

    if start_service:
        # define and start a database service
        database_service = client.V1Service(
            metadata=client.V1ObjectMeta(name="database"),
            spec=client.V1ServiceSpec(
                selector={"app": "database"},
                ports=[client.V1ServicePort(name="database", port=5432, target_port=5432)],
                type="ClusterIP"
            )
        )
        v1.create_namespaced_service(body=database_service, namespace="default")