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
        self.cursor.execute("CREATE TABLE IF NOT EXISTS metrics (service varchar(255), resource varchar(255), value double precision, timestamp timestamp)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS predicted_metrics (service varchar(255), resource varchar(255), value double precision, timestamp timestamp)")

    def insert_metric(self, table, service, resource, value, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow().replace(microsecond=0)
        self.cursor.execute("INSERT INTO {table} (service, resource, value, timestamp) VALUES (%s, %s, %s, %s)"
                            .format(table=table), (service, resource, value, ts))
        self.connection.commit()
    
    def drop_table(self, table):
        self.cursor.execute("DROP TABLE {table};".format(table=table))
        self.connection.commit()

    def get_data(self, table, service, resource):
        self.cursor.execute("SELECT * FROM {table} WHERE resource = '{resource}' AND service = '{service}'"
                            .format(table=table, resource=resource, service=service))
        rows = self.cursor.fetchall()
        return rows

    # returns all the rows where the timestamp is between utcnow - time & utcnow + time
    # where time is the time in minutes
    def get_data_from_date(self, hour, minutes):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        ts_minus = ts - timedelta(hours=hour, minutes=minutes)
        ts_plus = ts + timedelta(hours=hour, minutes=minutes)
        self.cursor.execute("SELECT * FROM metrics WHERE timestamp <= %s AND timestamp >= %s", (ts_plus, ts_minus))
        rows = self.cursor.fetchall()
        return rows

    def get_historical_data(self, table):
        self.cursor.execute("SELECT service, resource, value, timestamp FROM {table}".format(table=table))
        rows = self.cursor.fetchall()
        return rows
    
    def close_connection(self):
        self.cursor.close()
        self.connection.close()