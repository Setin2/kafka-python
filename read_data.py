import database

def main():
    data_base = database.Database()
    rows = data_base.get_data("service1", "CPU")

    for row in rows:
        print(row)
    
    data_base.close_connection()

if __name__ == '__main__':
    main()