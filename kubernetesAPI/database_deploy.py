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
                                    client.V1EnvVar(name="POSTGRES_USER", value=variables.POSTGRES_USER),
                                    client.V1EnvVar(name="POSTGRES_PASSWORD", value=variables.POSTGRES_PASSWORD)
                                ],
                                ports=[client.V1ContainerPort(container_port=variables.DATABASE_PORT)],
                                volume_mounts=[client.V1VolumeMount(name=variables.DATABASE_VOLUME_NAME, mount_path="/var/lib/postgresql/data")]
                            )
                        ],
                        volumes=[client.V1Volume(name=variables.DATABASE_VOLUME_NAME, empty_dir={})]
                    )
                )
            )
        )
        apps_v1.create_namespaced_deployment(body=database_deployment, namespace=namespace)

    if start_service:
        # define and start a database service
        database_service = client.V1Service(
            metadata=client.V1ObjectMeta(name="database"),
            spec=client.V1ServiceSpec(
                selector={"app": "database"},
                ports=[client.V1ServicePort(name="database", port=variables.DATABASE_PORT, target_port=variables.DATABASE_PORT)],
                type="ClusterIP"
            )
        )
        v1.create_namespaced_service(body=database_service, namespace=namespace)