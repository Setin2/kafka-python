from kafka import KafkaConsumer

"""
    For creating new consumers easily
"""
class Consumer:
    def __init__(self, topic, group):
        # To consume latest messages and auto-commit offsets
        self.consumer = KafkaConsumer(topic, group_id=group, bootstrap_servers=['localhost:9092'])
    
    def listen(self):
        for message in self.consumer:
            print({message.key.decode("utf-8"), message.value.decode("utf-8")})
            
            # consume earliest available messages, don't commit offsets
            KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)
            # StopIteration if no message after 1sec
            KafkaConsumer(consumer_timeout_ms=1000)
