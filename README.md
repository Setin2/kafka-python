# kafka-python

Monitor resource consumption for microservices using apache kafka, and allocate resources to the services in an optimal manner with the help of heuristics and ML.

## Broker, Zookeeper & Database

A kafka broker, zookeeper and a postgreSQL server can be initialized using the command ``` docker compose up -d ```

## Database

The file ``` database.py ``` contains a class for establishing a connection to the postgreSQL server, and various functions for writing/reading data to/from the database. 
The database table has the following format: ``` (taskID, serviceID, resourceID, value, timestamp) ```
The database also includes 2 lookup tables for the service/resource ID-name pairs: ``` (ID, name) ```
We need to save the service & resoruce as numerical values in the main table because we need to feed them into a neural net.

## Orchestrator

The file ``` order.JSON ``` contains the list of services that need to be applied to an image, and an ID of the order.
The JSON file is read by ``` orchestrator/orchestrator.py ```, which starts all the services in order, as well as a service that monitors their resource consumption.

## Monitor Producer

The file ``` monitor-producer/monitor-producer.py ``` is used by the orchestrator to spin up a producer for each service. The script requires the name of the service and the ID of the current order, which are provided automatically by the orchestrator.

## Monitoring

Before running the orchestrator, run the command ``` python monitor.py ```. It will start a consumer which will read the messages from the producers made for each service by the orchestrator. It will visualize the resource consumption of the given service using matplotlib.pyplot. The data from the producer is also stored in in timeseriesDB on the postgreSQL server.
This file also loads in our model, and predicts the expected resource consumption given the data read by the consumer. So we can visualise the real resource usage, and the predicted usage at the same time.
For now, we have to specify manually how many seconds we are in the task. Later this has to be done automatically. 

## Expected resource usage

The file ``` service_usage.py ``` can be used to get the expected minimum/average/maxmimum resource usage for each service-resource pair based on the data in our database. The simplest type of heuristics would be to assign resources based on these values (or rather, the maximum value).

## Training a model

The file ``` train.py ``` is used to train a neural network (its code can be seen in ``` network.py ```). The network takes in a list of services with all the unique services we run for a given task, a service-resource pair and a value representing for how many seconds we have been running the task for. The output should be how much of that resource, this service will be consuming at this point in time in the task.

The weights of the network and its optimizer can be saved in a ``` model_weights.pth ``` file. The loss during training can also saved in a ``` loss.png ``` file.

## Misc

The file ``` read_data.py ``` is simply a test file used to drop tables and read data using various function from ``` database.py ```.

Each example service has a folder with a dockerfile and kubernetes deployment files in it. Images can be build and run for the 2 services, but the kubernetes deployment files are not correctly configured yet.