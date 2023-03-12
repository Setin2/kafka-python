import database

def drop():
    data_base.drop_table("metrics")
    #data_base.drop_table("predicted_metrics")

def read():
    #rows = data_base.get_data("metrics", "service1", "CPU")
    #rows = data_base.get_data("predicted_metrics", "service1", "CPU")
    rows = data_base.get_data_from_date(1, 5)
    #rows = data_base.get_historical_data("metrics")

    for row in rows:
        print(row)

if __name__ == '__main__':
    data_base = database.Database()
    #drop()
    read()
    data_base.close_connection()