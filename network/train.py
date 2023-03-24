import torch
import network
import database
import pandas as pd
import torch.nn as nn
from torch.optim import Adam
import matplotlib.pyplot as plt

def train(model, optimizer, tasks):
    """
        Train by task group since then its easier to get the list of unique services for the task
        Dont feed batches to the network
    
        Args:
            model (network.ServiceValuePredictor Object): the model we wish to train
            optimizer (torch.optim Object): the optimizer of our model
            tasks ([DataFrame]): list of DataFrames where each DataFrame is a group of rows from the database for each task
        
        Returns:
            float: the cumulative loss for this epoch
    """
    cum_loss = 0
    task_group_start_index = 0
    for task_group in tasks:
        # keep track of the start index of this start group because we need it to compute the run-time
        task_group_start_index = task_group.index[0].tolist()
        unique_services = list(task_group['serviceID'].unique())
        # for each row in the task group
        for i in task_group.index.tolist():
            run_time = (task_group['timestamp'][i] - task_group['timestamp'][task_group_start_index]).total_seconds()
            current_service = task_group['serviceID'][i]
            current_resource = task_group['resourceID'][i]
            current_value = torch.tensor([task_group['value'][i]], dtype=torch.float32)

            # inputs = current service-resource pair, how much time went since we started the task (in seconds), 
            # and a list of all the unique services that are run in this task 
            inputs = unique_services + [current_service] + [current_resource] + [run_time]
            inputs = torch.tensor(inputs, dtype=torch.float32)

            # Forward pass: the output should be the value representing the resource consumption for that service-resource pair
            preds = model(inputs)
            loss = nn.MSELoss()(preds, current_value)
            cum_loss += loss.data

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    return cum_loss

def plot_loss(ax, loss_list):
    ax.plot(loss_list)
    plt.pause(0.01)

def save_model(model, optimizer):
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, "model_weights.pth")

def main(EPOCHS, LR, load_model=True, savemodel=True, savefig=False):
    # create a pandas dataframe from all the data we acumulated
    data_base = database.Database()
    data = data_base.get_historical_data("metrics")
    data_base.close_connection()
    df = pd.DataFrame(data, columns=['taskID', 'serviceID', 'resourceID', 'value', 'timestamp'])

    # create and load the model
    model = network.ServiceValuePredictor(input_size=1)
    optimizer = Adam(model.parameters(), lr=LR)
    if load_model: model.load_model(optimizer, train=True)

    # we group the rows by task, each group a member of the list
    tasks = [d for _, d in df.groupby('taskID')]

    fig, ax = plt.subplots()
    ax.title.set_text('Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    loss_list = []

    for epoch in range(EPOCHS):
        loss = train(model, optimizer, tasks)
        loss_list.append(loss/len(data))

    print("final loss: ", loss_list[len(loss_list) - 1])
    plot_loss(ax, loss_list)
    if savefig: plt.savefig('loss.png')
    if savemodel: save_model(model, optimizer)

if __name__ == '__main__':
    main(EPOCHS=200, LR=0.001, load_model=True, savemodel=True, savefig=True)