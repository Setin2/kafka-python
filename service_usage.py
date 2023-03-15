import pandas as pd
import database
import math

def get_expected_resource_usage(grouped, data_base):
    for group, values in grouped:
        # Create a new DataFrame for the current service and resource type with shape (timestamp, value)
        data_df = pd.DataFrame({'datetime': values['datetime'], 'value': values['value']})
        data_df = data_df.set_index('datetime')

        # we would like the names of the service-resource pair instead of the IDs
        service = data_base.get_service_name_from_ID(group[0])[0]
        resource = data_base.get_resource_name_from_ID(group[1])[0]

        min_expected_usage = min(data_df['value'])
        sum_expected_usage = sum(data_df['value']) / len(data_df)
        max_expected_usage = max(data_df['value'])

        #print(f"Minimum expected {resource} usage for {service} is: {min_expected_usage}")
        #print(f"Average expected {resource} usage for {service} is: {sum_expected_usage}")

        # we round up to the nearest 10 to give some breathing room
        print(f"Maximum expected {resource} usage for {service} is: {math.ceil(max_expected_usage/ 10) * 10}")

def main():
    data_base = database.Database()
    print("How do you want to group the services: ")
    print("0. get all data ungrouped")
    print("1. get data for the next x hours")
    print("2. get data by service group")
    choice = int(input())
    data = []
    grouped = None

    if choice == 0:
        data = data_base.get_historical_data("metrics")
    elif choice == 1:
        data = data_base.get_data_for_next_x_hours(1, 0)
    elif choice == 2:
        data = data_base.get_data_by_service_group(("service1", "service2", "service3"))
    
    df = pd.DataFrame(data, columns=['image_ID', 'service', 'resource', 'value', 'datetime'])
    df['datetime'] = pd.to_datetime(df['datetime'])

    grouped = df.groupby(['service', 'resource'])
    get_expected_resource_usage(grouped, data_base)

if __name__ == '__main__':
    main()