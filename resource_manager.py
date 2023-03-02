import consumer
import producer

# Resources available to the system
MAX_RAM = 8000 # in MB
MAX_CPU = 100 # %
MAX_GPU = 100 # %

AVAILABLE_RAM = 8000 # in MB
AVAILABLE_CPU = 100 # %
AVAILABLE_GPU = 100 # %

# Create customer(s) for monitoring the resource consumption

producer = producer.Producer()
producer.send("100", "RAM")

consumer = consumer.Consumer("my-topic", "my-group")
consumer.listen()