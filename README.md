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

The file ``` predictive_scaling.py ``` will be used to train ML model(s) to predict the resource consumption based on different parameters. For now the prediction of resource consumption is done via a simple linear regression model (which of course gives very bad results).