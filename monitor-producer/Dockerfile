FROM python:3.8

# Install net-tools package to get the `ifconfig` command
RUN apt-get update && apt-get install -y net-tools

# Set the network configuration
ENV KAFKA_BOOTSTRAP_SERVERS broker.kafka-python:9092

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

ENTRYPOINT ["python", "monitor-producer.py"]
CMD []