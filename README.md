# kafka-python

Monitor resource consumption for microservices using apache kafka.

## Main

The files of type ``` order.JSON ``` contain a list of tasks that need to be applied to an image, and an ID.
The ``` app.py ``` script can be used to start the kafka and database services (see below), and load order files.
Once 1 or more order files are loaded, it will start 2 monitoring services for each order and an orchestrator/ingestion service that handles the orchestration of the tasks we need apply.

The orchestrator itself also works as a job inside the kubernetes cluster, and starts the tasks in the order given to it. 
It listens to the tasks on an ``` orchestrator ```  topic, and each time it gets a message from a task, it knows that the task has finished, and the next one needs to be started.

## Orchestrator

To be added later (the orchestrator doesnt do much rn)

### Permision

In order to start new jobs/pods from inside the kubernetes cluster, we must give permission to the orchestartor script. First, a serviceaccount must be created using ``` kubectl create serviceaccount orchestrator ```, and then, the role and rolebinding files from ``` ./kubernetesAPI/ ``` must be applied to the kubernetes cluster using ``` kubectl apply -f kubernetesAPI/role.yaml ```.

## Broker, Zookeeper & Database

A kafka broker, zookeeper and a postgreSQL server can be initialized through the main script. The kafka bootstrap servers, database credidentials, and other kubernetes variables will be given to each service as environment variables. The files used to start the deployments, services, and jobs reside in ``` ./kubernetesAPI/ ``` for now.

## Microservices

Each example service has a folder with a dockerfile, a main script, and a list of requirements. 
Images for the services can be build and pushed to docker hub using the bash file as follows ``` ./build_service.sh <image_name> ``` (remember to build an executable for the file first ``` chmod +x build_service.sh ```).

For a given order, all services/tasks will be given the list of required tasks, the name of the currently running task, and the ID of the order as arguments. This includes the monitoring services.

All tasks must use kafka producers as follows:
1. On task start, send a message type ``` key: ORDER, value: required_tasks:task_name:orderID ``` to the ``` "task" + orderID ``` topic. This will notify the monitoring producer (see below), that a new task has started, and that it needs to be monitored.
2. On task end, send a message type ``` key: PROGRESS, value: progress:output ``` to the ``` orchestrator topic ```. Here, ``` progress ``` is a string of all the outputs of previous tasks, separated by ``` : ``` symbols, and ``` output ``` is the output of this task. This will notify the orchestrator that the task is finished. The output of all tasks will also be sent as an argument to the tasks so that they dont have to listen using kafka.
3. On task end, send a message type ``` key: HALT, value: HALT ``` to the monitoring producer service. This will notify the monitoring producer that the task no longer needs to be monitored (but another task might start)
4. On task end, check if this was the last task in the order. If it was, send a message type ``` key: STOP, value: STOP ``` to the monitoring producer service. This will notify the monitoring producer service that it needs to terminate, as this order is finished. (The orchestrator doesnt need to be notified, as it can easliy check if the order is finished)

## Monitor Producer

The ``` monitor-producer ``` is used to start a consumer which listens to the tasks. If it gets a new message stating that the task has started, it will start sending messages type ``` key: required_tasks:task_name:orderID:resource_name, value: resource_usage ``` on the ``` "resource" + orderID ``` topic. Messages are sent by the resource producer every 1 second until it gets a message stating to to otherwise.

The monitor producer will also listen on the ``` "task" + orderID ``` topic. The messages it can get are as follows:
1. ORDER: this means that a new task has started.
2. HALT: this means that the order needs to stop monitoring the resources and wait until it gets a message from the next task.
3. STOP: this means that the order is finished and it needs to stop. If this happens, the monitor producer will forward this message on the ``` "resource" + orderID ``` topic (instad of a message with the resource consumption). This will notify the monitor consumer service that it needs to stop as well.
4. TERMINATE: This message is given by the monitor consumer service before terminating. This means that the monitor producer must also terminate.

The HALT, STOP, TERMINATE messages will probably be modified later to something more intuitive.

## Monitor Consumer

The monitor consumer service will listen to the ``` "resource" + orderID ``` topic, for messages from the monitor-producer. 
The data from the producer is stored in timeseriesDB on the postgreSQL server.
The monitor consumer service can be used to visualize the resource consumption of each given task using matplotlib.pyplot (and later, it could be used to monitor the difference between the expected resource usage from a trained nerural net and the actual resource usage).

Besides messages containing the resource usage of some task, the monitoring consumer might get a message type ``` key: STOP, value: STOP ``` from the monitoring producer. This means that the service must terminate. Before stoping however, it will reply to the monitoring producer with a message type ``` key: TERMINATE, value: TERMINATE ```, notifying that all monitoring for this order must stop.

## Database

The file ``` database.py ``` contains a class for establishing a connection to the postgreSQL server, and various functions for writing/reading data to/from the database. The database table has the following format: ``` (orderID, taskID, resourceID, value, timestamp) ```
The database also includes 2 lookup tables for the service/resource ID-name pairs: ``` (ID, name) ```
We need to save the task & resource as numerical values in the main table because we need to feed them into a neural net.
