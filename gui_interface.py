import json
import tkinter as tk
from tkinter import filedialog
from kubernetesAPI import database_deploy
from kubernetesAPI import kafka_broker_deploy
from kubernetesAPI import kafka_zookeeper_deploy

class GUI:
    def __init__(self, title="GUI Example"):
        # Create the main window
        self.root = tk.Tk()
        self.root.title(title)
        self.orders = []

        self.output = None
        self.create_buttons()
    
    def start(self):
        self.root.mainloop()
    
    def create_buttons(self):
        # Create buttons and output field using grid layout
        database_button = tk.Button(self.root, text="Database", command=self.on_create_database_click, bg="red", fg="white", font=("Helvetica", 12, "bold"))
        database_button.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        database_delete_button = tk.Button(self.root, text="Delete", command=self.on_delete_database, bg="red", fg="white", font=("Helvetica", 8, "bold"))
        database_delete_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        zookeeper_button = tk.Button(self.root, text="Zookeeper", command=self.on_create_zookeeper_click, bg="red", fg="white", font=("Helvetica", 12, "bold"))
        zookeeper_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        zookeeper_delete_button = tk.Button(self.root, text="Delete", command=self.on_delete_zookeeper, bg="red", fg="white", font=("Helvetica", 8, "bold"))
        zookeeper_delete_button.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        broker_button = tk.Button(self.root, text="Broker", command=self.on_create_broker_click, bg="red", fg="white", font=("Helvetica", 12, "bold"))
        broker_button.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        broker_delete_button = tk.Button(self.root, text="Delete", command=self.on_delete_broker, bg="red", fg="white", font=("Helvetica", 8, "bold"))
        broker_delete_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.output = tk.Text(self.root, height=10, width=30)
        self.output.grid(row=4, columnspan=2)

    # Methods for starting the database, zookeeper, and broker services & deployments. The GUI buttons are used to run these.
    def on_create_database_click(self):
        database_deploy.create_database(start_deployment=True, start_service=False)
        self.output.insert(tk.END, "Database is running...\n")
        #database_button.configure(bg="green")

    def on_create_zookeeper_click(self):
        kafka_zookeeper_deploy.create_zookeeper(start_deployment=True, start_service=False)
        self.output.insert(tk.END, "Zookeeper is running...\n")
        #zookeeper_button.configure(bg="green")

    def on_create_broker_click(self):
        kafka_broker_deploy.create_broker(start_deployment=True, start_service=False)
        self.output.insert(tk.END, "Broker is running...\n")
        #broker_button.configure(bg="green")

    # Methods for deleting the database, zookeeper, and broker services & deployments. The GUI buttons are used to run these.
    def on_delete_database(self):
        kubernetes_job.delete_deployment_and_service("database", delete_deployment=True, delete_service=False)
        self.output.insert(tk.END, "Database deleted.\n")
        #database_button.configure(bg="red")

    def on_delete_zookeeper(self):
        kubernetes_job.delete_deployment_and_service("zookeeper", delete_deployment=True, delete_service=False)
        self.output.insert(tk.END, "Zookeeper deleted.\n")
        #zookeeper_button.configure(bg="red")

    def on_delete_broker(self):
        kubernetes_job.delete_deployment_and_service("kafka-broker", delete_deployment=True, delete_service=False)
        self.output.insert(tk.END, "Broker deleted.\n")
        #broker_button.configure(bg="red")