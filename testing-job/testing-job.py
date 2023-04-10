import os
import database

def drop():
    data_base.drop_table("metrics")
    data_base.drop_table("service_lookup")
    data_base.drop_table("resource_lookup")

def read():
    #rows = data_base.get_data("service1", "CPU")
    #rows = data_base.get_data_for_next_x_hours(1, 5)
    #rows = data_base.get_data_by_service_group(("service1", "service2"))
    #data_base.delete_row("metrics", "taskID", 7)
    print("called", flush=True)
    rows = data_base.get_historical_data("metrics")
    print("called2", flush=True)

    print(rows, flush=True)

    for row in rows:
        print(row, flush=True)

if __name__ == '__main__':
    host, port = os.getenv("POSTGRES_HOST").split(":")
    dbname = os.getenv("POSTGRES_NAME")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    data_base = database.Database(host, port, dbname, user, password)
    #drop()
    read()
    data_base.close_connection()