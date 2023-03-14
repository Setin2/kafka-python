import os
import torch
import network
from torch.optim import Adam

def load_model():
    model = network.ServiceValuePredictorRNN(1, 64)
    optimizer = Adam(model.parameters(), lr=0.001)
    if os.path.exists("model_weights.pth"):
        checkpoint = torch.load('model_weights.pth')
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        model.eval()
        #model.train()
    return model

def main():
    model = load_model()
    with torch.no_grad():
        test_inputs = [2, 1, 3] + [1] + [1] + [2]
        test_inputs = torch.tensor(test_inputs, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
        prediction = model(test_inputs)
        print(prediction)

if __name__ == '__main__':
    main()