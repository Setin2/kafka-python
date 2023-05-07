import os
import json
import producer
from flask import Flask, request

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
start_producer = producer.Producer("orchestrator", kafka_bootstrap_servers)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_request():
    data = request.get_json()
    print(data)
    start_producer.send("START", json.dumps(data))
    return "OK"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9092)
