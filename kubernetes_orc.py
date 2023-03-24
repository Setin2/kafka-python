from kubernetes import client, config, watch
import json
import time

# Dont know, some things we need to do stuff
config.load_kube_config()
namespace = "default"
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

def create_zookeeper():
    # Define Zookeeper deployment
    zookeeper = client.V1Deployment(
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

    # Define Zookeeper service
    zookeeper_service = client.V1Service(
        metadata=client.V1ObjectMeta(name="zookeeper"),
        spec=client.V1ServiceSpec(
            selector={"app": "zookeeper"},
            ports=[client.V1ServicePort(port=2181)]
        )
    )

    # Create the Zookeeper deployment and service in the Kubernetes cluster
    apps_v1.create_namespaced_deployment(body=zookeeper, namespace="default")
    #v1.create_namespaced_service(body=zookeeper_service, namespace="default")

def create_broker():
    # Define the Kafka broker deployment
    broker = {
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

    # Define Zookeeper service
    broker_service = client.V1Service(
        metadata=client.V1ObjectMeta(name="kafka-broker"),
        spec=client.V1ServiceSpec(
            selector={"app": "kafka-broker"},
            ports=[client.V1ServicePort(port=9092)]
        )
    )

    # Create the Kafka broker deployment
    apps_v1.create_namespaced_deployment( body=broker, namespace="default" )
    #v1.create_namespaced_service(body=broker_service, namespace="default")

def create_database():
    # Define database deployment
    database = client.V1Deployment(
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

    apps_v1.create_namespaced_deployment(body=database, namespace="default")

    # Define database service
    database_service = client.V1Service(
        metadata=client.V1ObjectMeta(name="database"),
        spec=client.V1ServiceSpec(
            selector={"app": "database"},
            ports=[client.V1ServicePort(name="database", port=5432, target_port=5432)],
            type="ClusterIP"
        )
    )

    v1.create_namespaced_service(body=database_service, namespace="default")

def create_job(service_name, args=[]):
    """
        Create a kubernetes job with for a given service

        Args:
            service_name (str): name of the service that was tagged and pushed to a continer repository (like docker hub)
            args ([str]): list of arguments to give to the service container (generally for the monitoring producer server)
        
        Returns:
            kubernetes.client.BatchV1Api.V1Job: the kubernetes job
    """
    # Define the YAML for the job
    job = client.V1Job()
    job.api_version = "batch/v1"
    job.kind = "Job"
    job.metadata = client.V1ObjectMeta(name=service_name)
    job.spec = client.V1JobSpec(
        completions=1,
        ttl_seconds_after_finished=1,  # Automatically delete the job after 1 second
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": service_name}),
            spec=client.V1PodSpec(
                restart_policy="Never",
                host_network=False,
                containers=[
                    client.V1Container(
                        name=service_name,
                        image=f"setin/{service_name}:latest",
                        command=["python", f"{service_name}.py"] + args,
                        ports=[client.V1ContainerPort(name="kafka-python", container_port=9092)],
                        env=[
                            client.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value="kafka-broker:9092"),
                            client.V1EnvVar(name="KAFKA_ZOOKEEPER_CONNECT", value="zookeeper:2181"),
                            client.V1EnvVar(name="POSTGRES_HOST", value="db:5432"),
                            client.V1EnvVar(name="POSTGRES_USER", value="postgres"),
                            client.V1EnvVar(name="POSTGRES_PASSWORD", value="postgres"),
                            client.V1EnvVar(name="POSTGRES_DB", value="mydatabase"),
                            client.V1EnvVar(name="SECRET_KEY", value="my-secret-key")
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
        Read the events for a service with the given name and wait for a success or failure event to terminate its corresponding monitoring service.

        Args:
            service_name (str): name of the service whose events we want to read
    """
    print(f"Waiting for {service_name} to complete...")
    w = watch.Watch()
    for event in w.stream(
        batch_v1.list_namespaced_job,
        namespace=namespace,
        label_selector=f"job-name={service_name}",
        timeout_seconds=0
    ):
        o = event["object"]

        if o.status.succeeded:
            print("Job finished succesfully")
            w.stop()
            return

        if not o.status.active and o.status.failed:
            w.stop()
            raise Exception("Job Failed")

#create_zookeeper()
#create_broker()
#create_database()
# Delete the deployment
def delete(service):
    deployment_name = service
    api_instance = client.AppsV1Api()
    api_instance.delete_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=client.V1DeleteOptions(),
    )

    # Delete the service
    service_name = service
    api_instance = client.CoreV1Api()
    api_instance.delete_namespaced_service(
        name=service_name,
        namespace=namespace,
        body=client.V1DeleteOptions(),
    )
#delete("zookeeper")
#delete("kafka-broker")
#delete("database")


# Read the file with the given order
with open("order.json", "r") as tasks_file:
    tasks = json.load(tasks_file)

#monitor_producer_job = create_job("monitor-producer")
#time.sleep(6)

# Start the required services in the order specified, a monitoring producer for each job
for service_name in tasks["required_services"]:
    service_job = create_job(service_name, [service_name, tasks["taskID"]])
    wait_for_job_completion(service_name)

#batch_v1.delete_namespaced_job(name="monitor-producer", namespace=namespace, body=client.V1DeleteOptions())

"""
to run the docker compose and the kubernetes cluster on the same server:

create the kafka-python namespace by with: 
    kubectl apply -f Namespace.YAML    

if container is ran separetly from kubernetes for some reson, start it on specific network with:
    docker run --network=kafka-python monitor-producer

example on building an image for docker hub for a certain service:
    docker build -t service1:latest service1
    docker tag service1:latest setin/service1:latest
    docker push setin/service1:latest
"""

#kafka.errors.NoBrokersAvailable: NoBrokersAvailable