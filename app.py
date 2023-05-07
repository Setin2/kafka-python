import time
import json
import random
import requests
import threading
import gui_interface
import tkinter as tk
from tkinter import filedialog
from kubernetesAPI import kubernetes_job
from kubernetesAPI import database_deploy
from kubernetesAPI import kafka_broker_deploy
from kubernetesAPI import kafka_zookeeper_deploy

url = "http://localhost:30820"  # replace {node_ip} with the IP address of any node in the cluster
data = {"key": "value"}  # replace with your data

orders = []

# first create the databse and the zookeeper
#database_deploy.create_database(start_deployment=True, start_service=False)
#kafka_zookeeper_deploy.create_zookeeper(start_deployment=True, start_service=False)

# give the zookeeper some time to start and then create the broker
#kafka_broker_deploy.create_broker(start_deployment=True, start_service=False)

# give the broker some time to start, then start the proxy service for sending orders
#kubernetes_job.create_service_and_deployment("proxy-server", start_deployment=True, start_service=False, service_type=2)

# then start the orchestrator and system monitor
#kubernetes_job.create_service_and_deployment("monitor-system", start_deployment=True, start_service=False)
#kubernetes_job.create_service_and_deployment("orchestrator", start_deployment=True, start_service=False)

# optional if you want to monitor resources as well (not working correctly rn)
#kubernetes_job.create_service_and_deployment("monitor-resources", start_deployment=True, start_service=False)

# then start the services for the tasks
#kubernetes_job.create_service_and_deployment("service1", start_deployment=True, start_service=False)
#kubernetes_job.create_service_and_deployment("service2", start_deployment=True, start_service=False)
#kubernetes_job.create_service_and_deployment("service3", start_deployment=True, start_service=False)

def on_load_json_files_click():
    """        
        Send orders as json data to the proxy service
    """
    file_paths = filedialog.askopenfilenames(
        title="Select orders",
        filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
    )
    # Load the JSON data and append it to list of loaded JSON files
    if file_paths:
        for file_path in file_paths:
            with open(file_path, "r") as file:
                order = json.load(file)
                order["orderID"] = random.randint(0, 400)
                response = requests.post(url, json=order)
                print(response.text)
    else:
        print("No files selected.")

def startGUI():
    gui = gui_interface.GUI()
    load_json_files_button = tk.Button(gui.root, text="Load Orders", command=on_load_json_files_click)
    load_json_files_button.grid(row=3, column=0, padx=10, pady=10, sticky="e")
    gui.start()

startGUI()