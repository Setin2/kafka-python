import os
import torch
import torch.nn as nn


class ServiceValuePredictor(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)

    def forward(self, inputs):
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
        if os.path.exists("model_weights.pth"):
            checkpoint = torch.load('model_weights.pth')
            self.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            if train: self.train()
            else: self.eval()
