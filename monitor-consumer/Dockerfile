FROM python:3.8

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

ENTRYPOINT ["python", "monitor-consumer.py"]
CMD []