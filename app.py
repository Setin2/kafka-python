import json
import time
import threading
import tkinter as tk
from tkinter import filedialog
from orchestrator import kubernetes_job
from orchestrator import database_deploy
from orchestrator import kafka_broker_deploy
from orchestrator import kafka_zookeeper_deploy

orders = []

# Methods for starting the database, zookeeper, and broker services & deployments. The GUI buttons are used to run these.
def on_create_database_click():
    database_deploy.create_database(start_deployment=True, start_service=False)
    output.insert(tk.END, "Database is running...\n")
    database_button.configure(bg="green")

def on_create_zookeeper_click():
    kafka_zookeeper_deploy.create_zookeeper(start_deployment=True, start_service=False)
    output.insert(tk.END, "Zookeeper is running...\n")
    zookeeper_button.configure(bg="green")

def on_create_broker_click():
    kafka_broker_deploy.create_broker(start_deployment=True, start_service=False)
    output.insert(tk.END, "Broker is running...\n")
    broker_button.configure(bg="green")

# Methods for deleting the database, zookeeper, and broker services & deployments. The GUI buttons are used to run these.
def on_delete_database():
    kubernetes_job.delete_deployment_and_service("database", delete_deployment=True, delete_service=False)
    output.insert(tk.END, "Database deleted.\n")
    database_button.configure(bg="red")

def on_delete_zookeeper():
    kubernetes_job.delete_deployment_and_service("zookeeper", delete_deployment=True, delete_service=False)
    output.insert(tk.END, "Zookeeper deleted.\n")
    zookeeper_button.configure(bg="red")

def on_delete_broker():
    kubernetes_job.delete_deployment_and_service("kafka-broker", delete_deployment=True, delete_service=False)
    output.insert(tk.END, "Broker deleted.\n")
    broker_button.configure(bg="red")

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
        required_tasks = str(order["required_tasks"])
        orchestrator_job = kubernetes_job.create_job("orchestrator", [orderID, required_tasks])

        # wait for the orchestrator to either finish successfully or fail in a separate thread
        # start a new thread to monitor the orchestrator job
        thread = threading.Thread(target=kubernetes_job.wait_for_job_completion, args=("orchestrator-" + orderID,))
        thread.start()

        # store the thread object in a list to join them later
        threads.append(thread)

    # wait for all threads to complete before exiting the function
    for thread in threads:
        thread.join()

"""        
    Load the JSON files with the orders. The GUI buttons are used to run this method
"""
def on_load_json_files_click():
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
                output.insert(tk.END, f"Orders have been loaded.\n")
    else:
        output.insert(tk.END, "No files selected.\n")
    start_orchestrator()

job = kubernetes_job.create_job("testing-job", ["1"])

# Create the main window
root = tk.Tk()
root.title("GUI Example")

# Create buttons and output field using grid layout
database_button = tk.Button(root, text="Database", command=on_create_database_click, bg="red", fg="white", font=("Helvetica", 12, "bold"))
database_button.grid(row=0, column=0, padx=10, pady=10, sticky="e")
database_delete_button = tk.Button(root, text="Delete", command=on_delete_database, bg="red", fg="white", font=("Helvetica", 8, "bold"))
database_delete_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")

zookeeper_button = tk.Button(root, text="Zookeeper", command=on_create_zookeeper_click, bg="red", fg="white", font=("Helvetica", 12, "bold"))
zookeeper_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
zookeeper_delete_button = tk.Button(root, text="Delete", command=on_delete_zookeeper, bg="red", fg="white", font=("Helvetica", 8, "bold"))
zookeeper_delete_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")

broker_button = tk.Button(root, text="Broker", command=on_create_broker_click, bg="red", fg="white", font=("Helvetica", 12, "bold"))
broker_button.grid(row=2, column=0, padx=10, pady=10, sticky="e")
broker_delete_button = tk.Button(root, text="Delete", command=on_delete_broker, bg="red", fg="white", font=("Helvetica", 8, "bold"))
broker_delete_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")

load_json_files_button = tk.Button(root, text="Load Orders", command=on_load_json_files_click)
load_json_files_button.grid(row=3, column=0, padx=10, pady=10, sticky="e")

output = tk.Text(root, height=10, width=30)
output.grid(row=4, columnspan=2)

root.mainloop()