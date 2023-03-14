import torch.nn as nn
import torch.nn.functional as F
import torch
from torch.nn.utils.rnn import pack_sequence, pad_packed_sequence

class ServiceValuePredictor(nn.Module):
    def __init__(self, input_size, hidden_size=128, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)

    def forward(self, inputs):
        # Add an extra dimension to input tensor to make it 2D
        #inputs = inputs.unsqueeze(0).unsqueeze(-1)
        # Reshape input tensor to have batch size of 1
        inputs = inputs.reshape(1, -1, 1)

        # Pass input sequence through LSTM layer
        _, (h_n, _) = self.lstm(inputs)

        # Pass final hidden state through fully connected layers
        x = torch.relu(self.fc1(h_n[-1]))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x.squeeze()

class ServiceValuePredictorRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.rnn = nn.GRU(input_size=input_size, hidden_size=hidden_size, num_layers=1, batch_first=True)
        self.attention = nn.Linear(hidden_size, hidden_size)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        batch_size, seq_len, input_size = x.size()  # get the input size and sequence length
        h0 = torch.zeros(1, batch_size, self.rnn.hidden_size).to(x.device)  # initialize the hidden state
        out, h_n = self.rnn(x, h0)  # pass the input through the RNN
        attn_weights = torch.softmax(self.attention(out), dim=1)  # compute attention weights over the sequence
        context = torch.bmm(attn_weights.transpose(1, 2), out)  # compute a weighted sum of the hidden states
        out = self.fc(context.squeeze(dim=1))  # pass the weighted sum through a linear layer
        return out
