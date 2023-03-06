"""import psutil
from kafka import KafkaProducer
import time

KAFKA_TOPIC = 'resource-monitor'
KAFKA_BOOTSTRAP_SERVERS = 'kafka-broker:9092'

def get_cpu_usage():
    return psutil.cpu_percent()

def get_memory_usage():
    mem = psutil.virtual_memory()
    return mem.percent

def send_resource_data(producer, cpu_usage, mem_usage):
    data = {'cpu_usage': cpu_usage, 'mem_usage': mem_usage}
    producer.send(KAFKA_TOPIC, value=data)

if __name__ == '__main__':
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    while True:
        cpu_usage = get_cpu_usage()
        mem_usage = get_memory_usage()
        send_resource_data(producer, cpu_usage, mem_usage)

        # Wait for 5 seconds before collecting and sending next data point
        time.sleep(5)
"""
print("Monitoring")