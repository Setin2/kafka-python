import time
import sys
sys.path.append('../')
import producer

x = 0

time.sleep(20)

print("hello from service1")

producer = producer.Producer()
producer.send("orchestrator", "message", "done")