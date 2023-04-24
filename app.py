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

orders = []

"""
kubernetes_job.create_service_and_deployment("service1")
kubernetes_job.create_service_and_deployment("service2")
kubernetes_job.create_service_and_deployment("service3")
"""

"""        
    For each order loaded so far, we start an orchestrator job and send it the order.
"""
def start_orchestrator():
    threads = []
    for i, order in enumerate(orders):
        orderID = order["orderID"]
        print(f"Starting order nr.{i + 1} with ID {orderID}")
        # start monitoring this order
        monitor_consumer_job = kubernetes_job.create_job("monitor-consumer", [orderID])
        monitor_producer_job = kubernetes_job.create_job("monitor-producer", [orderID])
        # add some delay between jobs
        time.sleep(5)

        # extract the order details and send them to the orchestrator job
        orchestrator_input = f"""{{
            "input": {5},
            "orderID": {orderID},
            "required_tasks": {json.dumps(order['required_tasks'])},
            "done": {json.dumps(order['completed_tasks'])}
        }}"""
        orchestrator_job = kubernetes_job.create_job("orchestrator", [orderID, str(orchestrator_input)])

        # wait for the orchestrator to either finish successfully or fail in a separate thread
        # start a new thread to monitor the orchestrator job
        thread = threading.Thread(target=kubernetes_job.wait_for_job_completion, args=("orchestrator-" + order["orderID"],))
        thread.start()

        # store the thread object in a list to join them later
        threads.append(thread)

    # wait for all threads to complete before exiting the function
    for thread in threads:
        thread.join()

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
                json_data = json.load(file)
                orders.append(json_data)
                print("Orders have been loaded.")
    else:
        print("No files selected.")
    start_orchestrator()

#job = kubernetes_job.create_job("testing-job", ["1"])

gui = gui_interface.GUI(start_orchestrator)
load_json_files_button = tk.Button(gui.root, text="Load Orders", command=on_load_json_files_click)
load_json_files_button.grid(row=3, column=0, padx=10, pady=10, sticky="e")
gui.start()