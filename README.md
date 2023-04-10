# kafka-python

Monitor resource consumption for microservices using apache kafka, and allocate resources to the services in an optimal manner with the help of heuristics and ML.

## Orchestrator

The file ``` order.JSON ``` contains the list of services that need to be applied to an image, and an ID of the order.
The JSON file is read by ``` kubernetes_orc.py ```, which starts all the services in order, as well as the services used to monitor their resource consumption.

## Broker, Zookeeper & Database

A kafka broker, zookeeper and a postgreSQL server will be initialized by the kubernetes orchestartor script. The kafka bootstrap servers and database credidentials will be given to each service as environment variables. The files used by the kubernetes orchestrator to start the deployments, services, and jobs reside in ``` ./kubernetes_api ```

## Services

Each example service has a folder with a dockerfile a main script, and a list of requirements. 
Images for the services can be build and pushed to docker hub using the bash file as follows ``` ./build_service.sh <image_name> ``` (an executable needs to be created for the file first ``` chmod +x build_service.sh ```).

If the container is ran separetly from kubernetes for some reson, start it on specific network with: ``` docker run --network=kafka-python monitor-producer ```.

## Monitor Producer

The ``` monitor-producer ``` is used by the orchestrator to spin up a consumer which listens to the services. If it gets a new message from some service, it will start producer which sends messages on a ``` resources ``` topic about the resource consumption of the last service that sent it a message. Messages are sent by the resource producer every 1 second.
The orchestrator starts the monitor-producer job before starting any of the services, and finishes it once all the services in the orders file have been completed.

## Monitor Consumer

Before running the monitor producer, the orchestrator will start a consumer which will read the messages from its producer.

The monitor consumer service will visualize the resource consumption of the given service using matplotlib.pyplot. 
The data from the producer is also stored in timeseriesDB on the postgreSQL server.

## Database

The shared file ``` database.py ``` contains a class for establishing a connection to the postgreSQL server, and various functions for writing/reading data to/from the database. The database table has the following format: ``` (taskID, serviceID, resourceID, value, timestamp) ```
The database also includes 2 lookup tables for the service/resource ID-name pairs: ``` (ID, name) ```
We need to save the service & resource as numerical values in the main table because we need to feed them into a neural net.

## Expected resource usage

The file ``` service_usage.py ``` can be used to get the expected minimum/average/maxmimum resource usage for each service-resource pair based on the data in our database. The simplest type of heuristics would be to assign resources based on these values (or rather, the maximum value).

## Training a model

The file ``` train.py ``` is used to train a neural network (its code can be seen in ``` network.py ```). The network takes in a list of services with all the unique services we run for a given task, a service-resource pair and a value representing for how many seconds we have been running the task for. The output should be how much of that resource, this service will be consuming at this point in time in the task.

The weights of the network and its optimizer can be saved in a ``` model_weights.pth ``` file. The loss during training can also saved in a ``` loss.png ``` file.





kubectl create serviceaccount orchestrator

kubectl apply -f orchestrator/role.yaml

