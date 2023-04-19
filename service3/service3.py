import os
import time
import sys
import producer

required_tasks = sys.argv[1]
required_tasks = eval(required_tasks)
task_name = sys.argv[2]
orderID = sys.argv[3]
progress = sys.argv[4]

print("Topic = task" + orderID, flush=True)

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
monitoring_producer = producer.Producer("task" + orderID, kafka_bootstrap_servers)
orchestrator_producer = producer.Producer("orchestrator", kafka_bootstrap_servers)

future1 = monitoring_producer.send(str(required_tasks) + ":" + task_name, orderID)
result = future1.get(timeout=5)
if result:
    print('Message monitoring_producer sent successfully!')
else:
    print('Failed to send monitoring_producer message.')

time.sleep(4)

output = "Hello from service3"
print("We got the output " + output, flush=True)

future2 = orchestrator_producer.send("PROGRESS", progress + ":" + output)
result = future2.get(timeout=5)
if result:
    print('Message orchestrator_producer sent successfully!')
else:
    print('Failed to send orchestrator_producer message.')

if task_name in required_tasks[len(required_tasks) - 1]:
    future3 = monitoring_producer.send("STOP", "STOP")
    result = future3.get(timeout=5)
    if result:
        print('Message orchestrator_producer2 sent successfully!')
    else:
        print('Failed to send orchestrator_producer2 message.')