import psycopg2.pool
import psycopg2
import datetime
from datetime import timedelta

class Database():
    def __init__(self):
        pool = psycopg2.pool.SimpleConnectionPool(
            host="localhost",
            port="5432",
            dbname="postgres",
            user="postgres",
            password="postgres",
            minconn=1,
            maxconn=1  # set maxconn to 1 to disable pooling
        )
        self.connection = pool.getconn()
        pool.putconn(self.connection)
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS metrics (image_ID varchar(255), service varchar(255), resource varchar(255), value double precision, timestamp timestamp)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS predicted_metrics (image_ID varchar(255), service varchar(255), resource varchar(255), value double precision, timestamp timestamp)")

    def insert_metric(self, table, image_ID, service, resource, value, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow().replace(microsecond=0)
        self.cursor.execute("INSERT INTO {table} (image_ID, service, resource, value, timestamp) VALUES (%s, %s, %s, %s, %s)"
                            .format(table=table), (image_ID, service, resource, value, ts))
        self.connection.commit()
    
    def drop_table(self, table):
        self.cursor.execute("DROP TABLE {table};".format(table=table))
        self.connection.commit()
        print(f"Dropped table {table}")

    def get_data(self, table, service, resource):
        self.cursor.execute("SELECT * FROM {table} WHERE resource = '{resource}' AND service = '{service}'"
                            .format(table=table, resource=resource, service=service))
        rows = self.cursor.fetchall()
        return rows

    # returns all the rows where the data was stored between the current time, and timedelta(hours=hour, minutes=minutes) in the future
    def get_data_for_next_x_hours(self, hour, minutes):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        ts_plus = ts + timedelta(hours=hour, minutes=minutes)
        self.cursor.execute("SELECT * FROM metrics WHERE timestamp >= %s AND timestamp <= %s", (ts, ts_plus))
        rows = self.cursor.fetchall()
        if not rows:
            print(f"No data found for the next {hour} hours and {minutes} minutes. No service is usually running in this timespan.")
        return rows

    """
        A task (group of services) will be applied to an image
        Given a list of services, return the rows where all the services in the list have been applied to the same single image
        The rows are groupd by images
    """
    def get_data_by_service_group(self, list_of_services):
        self.cursor.execute(
            "SELECT t1.image_ID, t1.service, t1.resource, t1.value, t1.timestamp "
            "FROM metrics t1 "
            "WHERE t1.service IN %s "
            "AND NOT EXISTS ( "
            "SELECT t2.service "
            "FROM metrics t2 "
            "WHERE t2.image_ID = t1.image_ID "
            "AND t2.service NOT IN %s "
            ") "
            "GROUP BY t1.image_ID, t1.service, t1.resource, t1.value, t1.timestamp "
            "HAVING COUNT(DISTINCT t1.service) = 1; ",
            (list_of_services, list_of_services)
        )
        rows = self.cursor.fetchall()
        return rows

    def get_historical_data(self, table):
        self.cursor.execute("SELECT * FROM {table}".format(table=table))
        rows = self.cursor.fetchall()
        return rows
    
    def close_connection(self):
        self.cursor.close()
        self.connection.close()