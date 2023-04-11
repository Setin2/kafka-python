# kafka-python

Monitor resource consumption for microservices using apache kafka, and allocate resources to the services in an optimal manner with the help of heuristics and ML.

## Orchestrator

The file ``` order.JSON ``` contains a list of tasks that need to be applied to an image, and an ID.
The ``` app.py ``` script opens a GUI, which can be used to start the kafka and database services (see below), and load order files.
Once 1 or more order files are loaded, it will start the monitoring services for each order and an orchestrator/ingestion service that handles the orchestration of the tasks we need apply.

The orchestrator itself also works as a job inside the kubernetes cluster, and starts the tasks in the order given to it, sending notifications to the monitoring jobs to notify them of the current working task.

### Permision

In order to start new jobs/pods from inside the kubernetes cluster, we must give permission to the orchestartor script. First, a serviceaccount must be created using ``` kubectl create serviceaccount orchestrator ```, and then, the role and rolebinding files from ``` ./orchestrator/ ``` must be applied to the kubernetes cluster using ``` kubectl apply -f orchestrator/role. yaml ```.

## Broker, Zookeeper & Database

A kafka broker, zookeeper and a postgreSQL server will be initialized by the main script. The kafka bootstrap servers and database credidentials will be given to each service as environment variables. The files used to start the deployments, services, and jobs reside in ``` ./orchestrator/ ```

## Microservices

Each example service has a folder with a dockerfile a main script, and a list of requirements. 
Images for the services can be build and pushed to docker hub using the bash file as follows ``` ./build_service.sh <image_name> ``` (an executable needs to be created for the file first ``` chmod +x build_service.sh ```).

(If the container is ran separetly from kubernetes for some reson, start it on specific network with: ``` docker run --network=kafka-python monitor-producer ```.)

## Monitor Producer

The ``` monitor-producer ``` is used to spin up a consumer which listens to the orchestrator. If it gets a new message, it will start a producer which sends messages on a ``` resources ``` topic about the resource consumption of the task specified in the message it got from the orchestrator. Messages are sent by the resource producer every 1 second.

## Monitor Consumer

The monitor consumer service will listen to the ``` resources ``` topic, for messages from the monitor-producer. It will visualize the resource consumption of each given task using matplotlib.pyplot. The data from the producer is also stored in timeseriesDB on the postgreSQL server.

## Database

The shared file ``` database.py ``` contains a class for establishing a connection to the postgreSQL server, and various functions for writing/reading data to/from the database. The database table has the following format: ``` (orderID, taskID, resourceID, value, timestamp) ```
The database also includes 2 lookup tables for the service/resource ID-name pairs: ``` (ID, name) ```
We need to save the task & resource as numerical values in the main table because we need to feed them into a neural net.

## Expected resource usage

The file ``` service_usage.py ``` can be used to get the expected minimum/average/maxmimum resource usage for each task-resource pair based on the data in our database. The simplest type of heuristics would be to assign resources based on these values (or rather, the maximum value).

## Training a model

The file ``` train.py ``` is used to train a neural network (its code can be seen in ``` network.py ```). The network takes in a list of services with all the unique services we run for a given task, a service-resource pair and a value representing for how many seconds we have been running the task for. The output should be how much of that resource, this service will be consuming at this point in time in the task.

The weights of the network and its optimizer can be saved in a ``` model_weights.pth ``` file. The loss during training can also saved in a ``` loss.png ``` file.

