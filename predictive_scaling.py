import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
from datetime import datetime, timedelta
import pandas as pd
import database

data_base = database.Database()
rows = data_base.get_historical_data("metrics")
data = []
for row in rows:
    data.append(row)

# Load the data into a pandas DataFrame
df = pd.DataFrame(data, columns=['service', 'resource', 'value', 'datetime'])
df['datetime'] = pd.to_datetime(df['datetime'])

# Group the data by service name and resource type
grouped = df.groupby(['service', 'resource'])

# Create a new DataFrame to store the predicted resource usage for each service and resource type
predicted_df = pd.DataFrame(columns=['service', 'resource', 'datetime', 'predicted_value'])

# Loop through each service and resource type and predict the future resource usage
for name, group in grouped:
    # Create a new DataFrame with the resource usage data for the current service and resource type
    data_df = pd.DataFrame({'datetime': group['datetime'], 'value': group['value']})
    data_df = data_df.set_index('datetime')
    
    # Resample the data to a fixed time interval (e.g. every 5 minutes)
    resampled_df = data_df.resample('5T').mean().fillna(method='ffill')
    
    # Create a new DataFrame with the datetime values for the next 12 hours
    next_12_hours = pd.DataFrame(pd.date_range(datetime.now(), datetime.now() + timedelta(hours=12), freq='5T'), columns=['datetime'])
    
    # Merge the resampled data with the next 12 hours of datetime values
    forecast_df = pd.merge_asof(left=resampled_df, right=next_12_hours, on='datetime', direction='forward')
    forecast_df = forecast_df.fillna(method='ffill')
    
    # Fit a linear regression model to the resampled data and predict the future resource usage
    X = pd.DataFrame({'timestamp': (forecast_df['datetime'] - datetime(1970,1,1)).dt.total_seconds()})
    y = forecast_df['value']
    model = LinearRegression().fit(X, y)

    next_12_hours['predicted_value'] = model.predict(pd.DataFrame({'timestamp': (next_12_hours['datetime'] - datetime(1970,1,1)).dt.total_seconds()}))
    
    # Add the predicted resource usage data to the predicted_df DataFrame
    next_12_hours['service'] = name[0]
    next_12_hours['resource'] = name[1]
    predicted_df = pd.concat([next_12_hours[['service', 'resource', 'datetime', 'predicted_value']], predicted_df])#predicted_df.append(next_12_hours[['service', 'resource', 'datetime', 'predicted_value']])

# Save the predicted resource usage data to the timeseriesDB
#for index, row in predicted_df.iterrows():
    #data_base.insert_metric("predicted_metrics", row['service'], row['resource'], row['predicted_value'], row['datetime'])
