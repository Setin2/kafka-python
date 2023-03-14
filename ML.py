import pandas as pd
import numpy as np
import database
import torch
import torch.nn as nn
import torch.optim as optim
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import Adam
from torch.nn.utils.rnn import pack_sequence, pad_packed_sequence
import operator
  
# Create a pandas dataframe from the data list
data_base = database.Database()
data = data_base.get_historical_data("metrics")
df = pd.DataFrame(data, columns=['taskID', 'serviceID', 'resourceID', 'value', 'timestamp'])

class ServiceValuePredictor(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)

    def forward(self, x):
        input_size = x.size(-1)  # get the size of the last dimension
        self.fc1 = nn.Linear(input_size, 64)  # adjust the input size of the first linear layer
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class RNN(nn.Module):
    # input size is simply used to determine the number of input features at each time step, and it does not constrain the length of the input sequence
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.rnn = nn.RNN(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x, h0, num_layers=1):
        # Define the RNN module
        rnn = nn.RNN(input_size=1, hidden_size=self.hidden_size, num_layers=num_layers)

        # Forward pass through the RNN
        out, hidden = rnn(x.unsqueeze(1), h0)

        # Flatten the output and pass it through a linear layer
        out = out.reshape(out.shape[0], -1)
        out = self.fc(out)

        return out

model = ServiceValuePredictor(input_size=1)
#RNN_model = RNN(1, 64, 18)
optimizer = Adam(model.parameters(), lr=0.001)
#RNN_optimizer = Adam(RNN_model.parameters(), lr=0.001)

tasks = [d for _, d in df.groupby(['taskID'])]


def train():
    cum_loss = 0
    task_group_cur_index = 0
    task_group_start_index = 0
    for task_group in tasks:
        #print(task_group)
        task_group_start_index = task_group_cur_index
        for i in range(len(task_group)):
            #print(task_group_cur_index)
            unique_services = list(task_group['serviceID'].unique())
            run_time = (task_group['timestamp'][task_group_cur_index] - task_group['timestamp'][task_group_start_index]).total_seconds()
            current_service = task_group['serviceID'][task_group_cur_index]
            current_resource = task_group['resourceID'][task_group_cur_index]
            current_value = torch.tensor([task_group['value'][task_group_cur_index]], dtype=torch.float32)

            inputs = unique_services + [current_service] + [current_resource] + [run_time]
            inputs = torch.tensor(inputs, dtype=torch.float32)

            # Forward pass
            preds = model(inputs)
            loss = nn.MSELoss()(preds, current_value)
            cum_loss += loss.data

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            task_group_cur_index += 1
    return cum_loss / task_group_cur_index

loss = 0
for epoch in range(500):
    loss = train()

print(loss)
test_inputs = [2, 1, 3] + [3] + [3] + [20]
test_inputs = torch.tensor(test_inputs, dtype=torch.float32)
prediction = model(test_inputs)
print(prediction)

data_base.close_connection()