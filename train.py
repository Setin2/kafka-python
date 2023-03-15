import torch
import network
import database
import pandas as pd
import torch.nn as nn
from torch.optim import Adam
import matplotlib.pyplot as plt

def train(model, optimizer, tasks):
    cum_loss = 0
    task_group_cur_index = 0
    task_group_start_index = 0
    """
        We train by task group since then its easier to get the list of unique services for the task
        We dont feed batches to the network but we need to keep track of how many forward passes we made
        Otherwise, when we move to the next task group, we start again from index 0, but the indices of the dataframes do not go back to 0
    """
    for task_group in tasks:
        # keep track of the start index of this start group because we need it to compute the run-time
        task_group_start_index = task_group_cur_index
        unique_services = list(task_group['serviceID'].unique())
        # for each row in the task group
        for _ in range(len(task_group)):
            run_time = (task_group['timestamp'][task_group_cur_index] - task_group['timestamp'][task_group_start_index]).total_seconds()
            current_service = task_group['serviceID'][task_group_cur_index]
            current_resource = task_group['resourceID'][task_group_cur_index]
            current_value = torch.tensor([task_group['value'][task_group_cur_index]], dtype=torch.float32)

            # we feed the network the current service-resource pair, how much time went since we started the task (in seconds), 
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
            task_group_cur_index += 1
    return cum_loss / task_group_cur_index

def plot_loss(ax, loss_list):
    ax.plot(loss_list)
    plt.pause(0.01)

def save_model(model, optimizer):
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, "model_weights.pth")

def main(EPOCHS, LR, savemodel=True, savefig=False):
    # Create a pandas dataframe from all the data we acumulated
    data_base = database.Database()
    data = data_base.get_historical_data("metrics")
    data_base.close_connection()
    df = pd.DataFrame(data, columns=['taskID', 'serviceID', 'resourceID', 'value', 'timestamp'])

    model = network.ServiceValuePredictor(input_size=1)
    optimizer = Adam(model.parameters(), lr=LR)
    model.load_model(optimizer, train=True)

    # we group the rows by task, each group a member of the list
    tasks = [d for _, d in df.groupby(['taskID'])]

    fig, ax = plt.subplots()
    ax.title.set_text('Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    loss_list = []

    for epoch in range(EPOCHS):
        loss = train(model, optimizer, tasks)
        loss_list.append(loss)

    print(loss_list)
    test_inputs = [20, 10, 30] + [20] + [20] + [20] # should be between 80 - 85
    test_inputs = torch.tensor(test_inputs, dtype=torch.float32)
    prediction = model(test_inputs)
    print(prediction)

    test_inputs = [20, 10, 30] + [10] + [10] + [20] # should be around 20
    test_inputs = torch.tensor(test_inputs, dtype=torch.float32)
    prediction = model(test_inputs)
    print(prediction)

    plot_loss(ax, loss_list)
    if savefig: plt.savefig('loss.png')
    if savemodel: save_model(model, optimizer)

if __name__ == '__main__':
    main(EPOCHS=100, LR=0.001, savemodel=True, savefig=False)