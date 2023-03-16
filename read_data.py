import database

def drop():
    data_base.drop_table("metrics")
    data_base.drop_table("service_lookup")
    data_base.drop_table("resource_lookup")

def read():
    #rows = data_base.get_data("service1", "CPU")
    #rows = data_base.get_data_for_next_x_hours(1, 5)
    #rows = data_base.get_data_by_service_group(("service1", "service2"))
    #data_base.delete_row("metrics", "resourceID", 0)
    rows = data_base.get_historical_data("metrics")

    for row in rows:
        print(row)

if __name__ == '__main__':
    data_base = database.Database()
    #drop()
    read()
    data_base.close_connection()