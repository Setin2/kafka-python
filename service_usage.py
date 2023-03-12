import pandas as pd
import database
import math

data_base = database.Database()
data = data_base.get_historical_data("metrics")
data = data_base.get_data_from_date(1, 0)

# Load the data into a pandas DataFrame
df = pd.DataFrame(data, columns=['service', 'resource', 'value', 'datetime'])
df['datetime'] = pd.to_datetime(df['datetime'])

# Group the data by service name and resource type
grouped = df.groupby(['service', 'resource'])

# Create a new DataFrame to store the predicted resource usage for each service and resource type
predicted_df = pd.DataFrame(columns=['service', 'resource', 'datetime', 'predicted_value'])

# Loop through each service and resource type and predict the future resource usage
for service_resource, values in grouped: # values = (service, resource, value, timestamp)
    # Create a new DataFrame for the current service and resource type with shape (timestamp, value)
    data_df = pd.DataFrame({'datetime': values['datetime'], 'value': values['value']})
    data_df = data_df.set_index('datetime')
    
    # Resample the data to a fixed time interval if needded (e.g. every 5 minutes)
    # resampled_df = data_df.resample('5T').mean().fillna(method='ffill')

    sum_expected_usage = sum(data_df['value']) / len(data_df)
    max_expected_usage = max(data_df['value'])
    min_expected_usage = min(data_df['value'])

    #print(f"Minimum usage for {service_resource} is: {min_expected_usage}")
    #print(f"Average usage for {service_resource} is: {sum_expected_usage}")
    
    # we round up to the nearest 10 to give some breathing room
    print(f"Maximum usage for {service_resource} is: {math.ceil(max_expected_usage/ 10) * 10}")