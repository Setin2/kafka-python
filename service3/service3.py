import time
import sys
sys.path.append('../')
import producer

time.sleep(4)

producer = producer.Producer()
producer.send("orchestrator", "message", "done3")
#producer.producer.flush()