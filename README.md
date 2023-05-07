# kafka-python

Monitor resource consumption for microservices using apache kafka.

## Broker, Zookeeper & Database

A kafka broker, zookeeper and a postgreSQL server can be initialized through the main script. The kafka bootstrap servers, database credidentials, and other kubernetes variables will be given to each service as environment variables. The files used to start the deployments and services reside in ``` ./kubernetesAPI/ ``` for now.

Images for the services can be build and pushed to docker hub using the bash file as follows ``` ./build_service.sh <image_name> ``` (remember to build an executable for the file first ``` chmod +x build_service.sh ```).

## Order Ingestion

The files of type ``` order.JSON ``` contain a list of tasks that need to be applied to an image, and an ID.
The ``` app.py ``` script can be used to start all necessary services, load order files, and send them to the ingestion service called ``` proxy-server ```

The ``` proxy-server ``` service uses ``` Flask ``` to listen to HTTP requests, where each request is an order.
It then sends each order further to the orchestrator service using apacha kafka. The reason for this approach is that we need to send messages using kafka only from within the kubernetes cluster. As the main application works outside of the cluster, we use HTTP requests to send orders.

## Orchestrator

The orchestrator itself listens on the kafka topic called ``` orchestrator ```. The messages it can get have the following keys:
1. On key ``` START ```, which it gets from the proxy server, the orchestrator will notify the system monitor that a new order has started, and then send the order to the service responsible for the first task in the order.
2. On key ``` SERVICE ```, which it gets from the system monitor, it will scale the deployment of a service (the number of replicas) as specified by the system monitor.
3. On key  ``` PROGRESS ```, which it gets from some service responsible for a task, it checks whether that was the last task in the order or not. If this was not the last task, it will send the order (which was modified by the previous task) to the next task in the order.

### Permision

In order to modify deployments from inside the kubernetes cluster, we must give permission to the orchestartor script. First, a serviceaccount must be created using ``` kubectl create serviceaccount orchestrator ```, and then, the role and rolebinding files from ``` ./kubernetesAPI/ ``` must be applied to the kubernetes cluster using ``` kubectl apply -f kubernetesAPI/role.yaml ```.

## System Monitor

The ``` monitor-system ``` service listens on a kafka topic called ``` system ``` for any changes in the system. The messages it can get have the following keys:
1. Key ``` ORDER ``` means that a new order has ben started. It will save the order in a list.
2. Key ``` INSTANCE ``` means that a deployment for some task has been scaled up/down. This is used to keep track of the number of replicas for each deployment.
3. Key ``` TASK ``` means that a new task in the order either started or finished, so it will save/delete the task from the list of active tasks. It then checks the number of running&upcoming orders that require the given task.

### Simple Heuristics

The system monitor is responsible for 2 very simple heuristics:
1. If the number of orders that require some task is bigger/smaller than some treshold, it will notify the orchestrator that the deployment for that service must be scaled up/down. Note however that the number of replicas for a services will depend on the number of partitions for its topic. If we have 5 consumers listening to messages from the orchestrator, but only 4 partitions, only 4 of the 5 replicas will actualy read the messages and do the computation. Changing the number of partitions for a topic is done as instructed in section "Kafka Configurations" and unfortunately done manually for now.
2. If the number of orders that require some task is 0, the service will start a thread with a timer. If the service has been idle for more than X amount of seconds, the last replica of that deployment will also be shut down in order to save resources. Similarly, if we get a new order that requires the task, the thread will be stopped.

## Tasks

Each task that needs to be applied to an image listens to a topic called after the task name. Once it gets a message, it does as follows:
1. Notify the system monitor (and the resource monitor) that it has started.
2. Perform some computation using the input from the order (which it always gets form the orchestrator)
3. Send the modified order back to the orchestrator.
4. (Notify the resource monitor that the task has ended and its resource consumption deosnt need to be monitored anymore)
5. If this was the last task in the order, notify the system monitor that the order is finished.
6. Then notify the system monitor that the task is finished as well.
The last 2 steps need to be performed in that order for the heuristics to work.

## Monitor Resources

The ``` monitor-resources ``` service listens to a kafka topic called ``` resource ```. 
The messages it gets indicate whether a new task has started or finished
1. In the case that a new task has started, it will read the CPU, RAM, and DISK usage of that task every 1 second, and insert the metrics into the database.
2. In the case where a task has finished (indicated by message key ``` HALT ```), it will simply remain idle until a new task starts.

The service can be used to visualize the resource consumption of each given task using matplotlib.pyplot (and later, it could be used to monitor the difference between the expected resource usage from a trained nerural net and the actual resource usage). For now however, the service is only able to listen to 1 task at a time.

## Database

The file ``` shared-files/database.py ``` contains a class for establishing a connection to the postgreSQL server, and various functions for writing/reading data to/from the database. The database table has the following format: ``` (orderID, taskID, resourceID, value, timestamp) ```
The database also includes 2 lookup tables for the service/resource ID-name pairs: ``` (ID, name) ```
We need to save the task & resource as numerical values in the main table because we need to feed them into a neural net.

## Kafka Configurations
Here are some usefull comands for debugging kafka and configuring it to work.

The partitions for a certain topic can be checked from inside the broker pod using the command:
``` kubectl exec -it <broker pod name> -- kafka-topics --bootstrap-server kafka-broker:9092 --describe --topic <topic name> ```

For now, the number of partitions has to be altered manually as such:
``` kubectl exec -it <broker pod name> -- kafka-topics --bootstrap-server kafka-broker:9092 --alter --topic <topic name> --partitions <num partitions> ```

To check the messages for a topic and to which partition they were assigned to, use the command:
``` kubectl exec -it kafka-broker-74d8cb676-nd82h -- kafka-console-consumer --bootstrap-server kafka-broker:9092 --topic service1 --from-beginning --property print.partition=true ```