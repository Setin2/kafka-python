import time
import sys
sys.path.append('../')
import producer

x = 0

time.sleep(4)

producer = producer.Producer()
producer.send("orchestrator", "message", "done")
#producer.producer.flush()