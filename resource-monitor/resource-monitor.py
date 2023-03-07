import psutil
import time
import producer

KAFKA_TOPIC = 'resource-monitor'
KAFKA_BOOTSTRAP_SERVERS = 'kafka-broker:9092'

def get_cpu_usage():
    return psutil.cpu_percent()

def get_memory_usage():
    mem = psutil.virtual_memory()
    return mem.percent

if __name__ == '__main__':
    #producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    producer = producer.Producer()

    while True:
        cpu_usage = get_cpu_usage()
        mem_usage = get_memory_usage()
        producer.send("my-topic", "CPU", str(cpu_usage))
        producer.send("my-topic", "RAM", str(mem_usage))

        # Wait for 5 seconds before collecting and sending next data point
        time.sleep(1)
