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
        self.output = tk.Text(self.root, height=10, width=30)
        self.output.grid(row=4, columnspan=2)