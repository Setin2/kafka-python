NAMESPACE = "default"
DOCKER_HUB_NAME = "setin"

# zookeeper config
ZOOKEEPER_NAME = "zookeeper"
ZOOKEEPER_PORT = "2181"
ZOOKEEPER_TICK_TIME = "2000"
ZOOKEEPER_IMAGE = "confluentinc/cp-zookeeper:7.3.0"

# broker config
BROKER_NAME = "kafka-broker"
BROKER_PORT = 9092
BROKER_IMAGE = "confluentinc/cp-kafka:7.3.0"
BROKER_VOLUME_NAME = "kafka-storage"
BROKER_VOLUME_MOUNT_PATH = "/var/lib/kafka/data"
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP = "PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT"
KAFKA_ADVERTISED_LISTENERS = "PLAINTEXT://localhost:29092,PLAINTEXT_INTERNAL://kafka-broker:9092"
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR = "1"
KAFKA_TRANSACTION_STATE_LOG_MIN_ISR = "1"
KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR = "1"

# database config
DATABASE_NAME = "database"
DATABASE_PORT = 5432
DATABASE_IMAGE = "postgres:14.1-alpine"
DATABASE_VOLUME_NAME = "database-volume"
DATABASE_VOLUME_MOUNT_PATH = "/var/lib/postgresql/data"

# job environment variables & config
KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"
KAFKA_ZOOKEEPER_CONNECT = "zookeeper:2181"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "database:5432"
POSTGRES_NAME = "postgres"
SERVICE_ACCOUNT_NAME = "orchestrator" # name of the job meant to start other jobs inside the cluster
