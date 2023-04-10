NAMESPACE = "default"

ZOOKEEPER_NAME = "zookeeper"
ZOOKEEPER_PORT = 2181

BROKER_NAME = "kafka-broker"
BROKER_PORT = 9092

DATABASE_NAME = "database"
DATABASE_PORT = 5432

KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"
KAFKA_ZOOKEEPER_CONNECT = "zookeeper:2181"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "database:5432"
POSTGRES_NAME = "postgres"

# Why is kubernetes inside my docker desktop stuck on "Starting ..."