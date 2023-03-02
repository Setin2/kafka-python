from kafka import KafkaConsumer

"""
    For creating new consumers easily
"""
class Consumer:
    def __init__(self, topic, group):
        # To consume latest messages and auto-commit offsets
        self.consumer = KafkaConsumer(topic, group_id=group, bootstrap_servers=['localhost:9092'])
        
        # consume earliest available messages, don't commit offsets
        KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)

        # StopIteration if no message after 1sec
        KafkaConsumer(consumer_timeout_ms=1000)
    
    def listen(self):
        for message in self.consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print ("%s %s" % (message.key, message.value))