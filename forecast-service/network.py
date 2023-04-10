import os
import torch
import torch.nn as nn

class ServiceValuePredictor(nn.Module):
    """
        Constructor for our model

        Args:
            input_size (int): size of the input at each time step
            hidden_size (int): number of LSTM hidden units, 128 by default
            num_layers (int): number of LSTM layers, 2 by default
            batch_first (bool): ensure that the input tensor has shape (batch_size, seq_len, input_size)

        Returns:
            ServiceValuePredictor: an untrained neural network with this architecture
    """
    def __init__(self, input_size, hidden_size=128, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)

    def forward(self, inputs):
        """
            Forward function of our network

            Args:
                inputs (torch.tensor([int])): a list of integer values representing service/resource IDs and task run-time
            
            Returns:
                torch.tensor([float]): a tensor representing the resource usage of that service
        """
        # Reshape input tensor to have batch size of 1
        inputs = inputs.reshape(1, -1, 1)

        # Pass input sequence through LSTM layer
        _, (h_n, _) = self.lstm(inputs)

        # Pass final hidden state through fully connected layers
        x = torch.relu(self.fc1(h_n[-1]))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x.squeeze(1)

    def load_model(self, optimizer, train=False):
        """
            Load the model and optimizer weights if previously trained

            Args:
                optimizer (torch.optim Object): the optimizer for our model
                train (bool): true for setting the model in training mode, false otherwise and by default
        """
        if os.path.exists("model_weights.pth"):
            checkpoint = torch.load('model_weights.pth')
            self.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            if train: self.train()
            else: self.eval()
