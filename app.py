import time
import json
import threading
import gui_interface
import tkinter as tk
from tkinter import filedialog
from kubernetesAPI import kubernetes_job
from kubernetesAPI import database_deploy
from kubernetesAPI import kafka_broker_deploy
from kubernetesAPI import kafka_zookeeper_deploy
import requests
import random

url = "http://localhost:30820"  # replace {node_ip} with the IP address of any node in the cluster
data = {"key": "value"}  # replace with your data

orders = []

#kubernetes_job.create_service_and_deployment("proxy-server", start_service=2)

#kubernetes_job.create_service_and_deployment("monitor-system")
#kubernetes_job.create_service_and_deployment("monitor-resources")
#kubernetes_job.create_service_and_deployment("orchestrator")

#kubernetes_job.create_service_and_deployment("service1", replicas=4)


#kubernetes_job.create_service_and_deployment("service1")
#kubernetes_job.create_service_and_deployment("service2")
#kubernetes_job.create_service_and_deployment("service3")


def on_load_json_files_click():
    """        
        Load the JSON files with the orders. The GUI buttons are used to run this method
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

#job = kubernetes_job.create_job("testing-job", ["1"])

gui = gui_interface.GUI()
load_json_files_button = tk.Button(gui.root, text="Load Orders", command=on_load_json_files_click)
load_json_files_button.grid(row=3, column=0, padx=10, pady=10, sticky="e")
gui.start()