import pandas as pd
import database
import math

data_base = database.Database()
#data = data_base.get_historical_data("metrics")
#data = data_base.get_data_for_next_x_hours(1, 0)
data = data_base.get_data_by_service_group(("service1", "service2", "service3"), timespan=3)

# Load the data into a pandas DataFrame
df = pd.DataFrame(data, columns=['image_ID', 'service', 'resource', 'value', 'datetime'])
df['datetime'] = pd.to_datetime(df['datetime'])

# Group the data by service name and resource type looping though them
grouped = df.groupby(['service', 'resource'])
for service_resource, values in grouped: # values = (image_ID, service, resource, value, timestamp)
    # Create a new DataFrame for the current service and resource type with shape (timestamp, value)
    data_df = pd.DataFrame({'datetime': values['datetime'], 'value': values['value']})
    data_df = data_df.set_index('datetime')

    sum_expected_usage = sum(data_df['value']) / len(data_df)
    max_expected_usage = max(data_df['value'])
    min_expected_usage = min(data_df['value'])

    #print(f"Minimum usage for {service_resource} is: {min_expected_usage}")
    #print(f"Average usage for {service_resource} is: {sum_expected_usage}")
    
    # we round up to the nearest 10 to give some breathing room
    print(f"Maximum usage for {service_resource} is: {math.ceil(max_expected_usage/ 10) * 10}")