import sys
import psutil
import time
import producer
import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

# kubernetes stuff, not relevant for now
KAFKA_TOPIC = 'resource-monitor'
KAFKA_BOOTSTRAP_SERVERS = 'kafka-broker:9092'

class Producer:
    def __init__(self):
        # To consume latest messages and auto-commit offsets
        self.producer = KafkaProducer()

    def on_send_success(self, record_metadata):
        print(record_metadata.topic)
        print(record_metadata.partition)
        print(record_metadata.offset)

    def on_send_error(self, excp):
        log.error('I am an errback', exc_info=excp)

    def send(self, topic, key, value, allow_callback=False):
        # produce asynchronously with callbacks
        if allow_callback:
            self.producer.send(topic, bytes(value, 'utf-8'), bytes(key, 'utf-8')).add_callback(self.on_send_success).add_errback(self.on_send_error)
        else:
            self.producer.send(topic, bytes(value, 'utf-8'), bytes(key, 'utf-8'))

        # block until all async messages are sent
        self.producer.flush()

def get_cpu_usage():
    return psutil.cpu_percent()

# RAM 
def get_memory_usage():
    mem_stats = psutil.virtual_memory()
    mem_total = mem_stats.total
    mem_used = mem_stats.used
    mem_percent = mem_stats.percent
    return mem_percent

def get_disk_usage():
    disk_stats = psutil.disk_usage('/')
    disk_total = disk_stats.total
    disk_used = disk_stats.used
    disk_percent = disk_stats.percent
    return disk_percent

if __name__ == '__main__':
    #producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    producer = Producer()

    # these should be collected automatically in the future
    service = sys.argv[1]
    taskID = sys.argv[2]

    while True:
        cpu_usage = get_cpu_usage()
        mem_usage = get_memory_usage()
        disk_usage = get_disk_usage()
        producer.send("resources", taskID + " " + service + " CPU", str(cpu_usage))
        producer.send("resources", taskID + " " +  service + " RAM", str(mem_usage))
        producer.send("resources", taskID + " " +  service + " DISK", str(disk_usage))

        # Wait for 1 second before collecting and sending next data point
        time.sleep(1)
