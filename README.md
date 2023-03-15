# kafka-python

## Broker, Zookeeper & Database

A kafka broker, zookeeper and a postgreSQL server can be initialized using the command ``` docker compose up -d ```

## Producer

For now, producers have to be started manually using the command ``` python producer/producer.py service_name image_ID ```.
Here, service_name is the name of the service currently running, and image_ID is the ID for the current task to which a list of services are applied.

## Consumer

To start a consumer, run the command ``` python monitor.py ```. The consumer will read the messages from the producer, and visualize the resource consumption of the given service using matplotlib.pyplot. The data from the producer is also stored in in timeseriesDB using psycog2.

## Database

The file ``` database.py ``` contains a class for establishing a connection to the postgreSQL server, and various functions for writing/reading data to/from the database. 
The database tables have the following format: ``` (image_ID, service, resource, value, timestamp) ```

### Expected resource usage

The file ``` service_usage.py ``` can be used to get the expected minimum/average/maxmimum resource usage for each service-resource pair based on the data in our database. The simplest type of heuristics would be to assign resources based on these values.

### Misc

The file ``` read_data.py ``` is simply a test file used to drop tables and read data using various function from ``` database.py ``` (without doing anything with the data)

Each example service has a folder with a dockerfile and kubernetes deployment files in it. Images can be build and run for the 2 services, but the kubernetes deployment files are not correctly configured yet. Thus, monitoring is done manually for now.

The file ``` train.py ``` is used to train a neural network (its code can be seen in ``` network.py ```). The network takes in a list of services with all the unique services we run for a given task, a service-resource pair and a value representing how long we have been running the task for. The output should be how much of that resource, this service will be consuming at this point in time in the task.

The weights of the network and its optimizer are saved in a ``` model_weights.pth ``` file. This file is loaded again in ``` test.py ``` to of course use the model (for now only for testing). The loss during training is also saved in a ``` .png ``` file.