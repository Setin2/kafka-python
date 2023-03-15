import torch
import network
from torch.optim import Adam

def load_model():
    model = network.ServiceValuePredictor(input_size=1)
    optimizer = Adam(model.parameters(), lr=0.001)
    model.load_model(optimizer)
    return model

def main():
    model = load_model()
    with torch.no_grad():
        test_inputs = [20, 10, 30] + [10] + [10] + [2]
        test_inputs = torch.tensor(test_inputs, dtype=torch.float32)
        prediction = model(test_inputs)
        print(prediction)

if __name__ == '__main__':
    main()