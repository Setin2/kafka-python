import os
import sys
import database

def drop():
    data_base.drop_table("metrics")
    #data_base.drop_table("task_lookup")
    #data_base.drop_table("resource_lookup")

def read():
    #rows = data_base.get_data("task1", "CPU")
    #rows = data_base.get_data_for_next_x_hours(1, 5)
    #rows = data_base.get_data_by_task_group(("task1", "task2"))
    #data_base.delete_row("metrics", "orderID", 7)
    rows = data_base.get_historical_data("metrics")

    for row in rows:
        print(row, flush=True)
    """rows = data_base.get_historical_data("task_lookup")

    for row in rows:
        print(row, flush=True)
    
    rows = data_base.get_historical_data("resource_lookup")

    for row in rows:
        print(row, flush=True)"""

if __name__ == '__main__':
    func = sys.argv[1]
    host, port = os.getenv("POSTGRES_HOST").split(":")
    dbname = os.getenv("POSTGRES_NAME")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    data_base = database.Database(host, port, dbname, user, password)
    if "0" in func:
        drop()
    elif "1" in func: read()
    data_base.close_connection()