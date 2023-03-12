from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import statsmodels.api as sm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
from datetime import datetime, timedelta
import pandas as pd
import database
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split

data_base = database.Database()
data = data_base.get_historical_data("metrics")

# Convert data to pandas DataFrame
df = pd.DataFrame(data, columns=['service', 'resource', 'value', 'timestamp'])
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Group the data by service name and resource type
grouped = df.groupby(['service', 'resource'])
predicted_df = pd.DataFrame(columns=['service', 'resource', 'predicted_value', 'timestamp'])

for service_resource, values in grouped: # values = (service, resource, value, timestamp)
    # Create a new DataFrame for the current service and resource type with shape (timestamp, value)
    data_df = pd.DataFrame({'timestamp': values['timestamp'], 'value': values['value']})
    data_df = data_df.set_index('timestamp')

    # Resample the data to a fixed time interval (e.g. every 5 minutes)
    resampled_df = data_df.resample('5S').mean().fillna(method='ffill')

    # Create sequences of length 50 and predict the next 50 * 5 minutes
    seq_length = 50
    X = []
    y = []
    for i in range(seq_length, len(resampled_df)):
        X.append(resampled_df.iloc[i-seq_length:i, 0])
        y.append(resampled_df.iloc[i, 0])
    X = np.array(X)
    y = np.array(y)

    # Normalize the data
    X_norm = X / np.max(X)
    y_norm = y / np.max(y)
    
    # Split the data into training and testing sets
    split_ratio = 0.8
    n_samples = len(X_norm)
    n_train = int(n_samples * split_ratio)
    X_train = X_norm[:n_train]
    y_train = y_norm[:n_train]
    X_test = X_norm[n_train:]
    y_test = y_norm[n_train:]

    # Reshape the data for the LSTM model
    n_features = 1
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], n_features))
    X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], n_features))

    # Define the LSTM model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(seq_length, n_features)))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mse')

    # Train the model
    history = model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

    future_preds = model.predict(X_test)
    # Print predicted values
    print(f"Predicted resource consumption for next {len(future_preds) * 5} minutes for {service_resource}:")
    print(future_preds)

"""
# Create a new DataFrame to store the predicted resource usage for each service and resource type
predicted_df = pd.DataFrame(columns=['service', 'resource', 'timestamp', 'predicted_value'])

# Loop through each service and resource type and predict the future resource usage
for name, group in grouped:
    # Create a new DataFrame with the resource usage data for the current service and resource type
    data_df = pd.DataFrame({'timestamp': group['timestamp'], 'value': group['value']})
    data_df = data_df.set_index('timestamp')
    
    # Resample the data to a fixed time interval (e.g. every 5 minutes)
    resampled_df = data_df.resample('5S').mean().fillna(method='ffill')
    
    # Create sequences of length 50 and predict the next 50 * 5 minutes
    seq_length = 50
    X = []
    y = []
    for i in range(seq_length, len(resampled_df)):
        X.append(resampled_df.iloc[i-seq_length:i, 0])
        y.append(resampled_df.iloc[i, 0])
    X = np.array(X)
    y = np.array(y)
    
    # Normalize the data
    X_norm = X / np.max(X)
    y_norm = y / np.max(y)
    
    # Split the data into training and testing sets
    split_ratio = 0.8
    n_samples = len(X_norm)
    n_train = int(n_samples * split_ratio)
    X_train = X_norm[:n_train]
    y_train = y_norm[:n_train]
    X_test = X_norm[n_train:]
    y_test = y_norm[n_train:]
    
    # Reshape the data for the LSTM model
    n_features = 1
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], n_features))
    X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], n_features))

    # Define the LSTM model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(seq_length, n_features)))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mse')

    # Train the model
    history = model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

    future_preds = model.predict(X_test)
    # Print predicted values
    print(f"Predicted resource consumption for next {len(future_preds) * 5} minutes for {name}-{group}:")
    print("++++++++++++++++++++++")
    print(future_preds)

"""
