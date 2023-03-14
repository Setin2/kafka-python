import psycopg2.pool
import psycopg2
import datetime
from datetime import timedelta

class Database():
    """
        The postgreSQL server is run in docker
    """
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
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                taskID int, 
                serviceID int, 
                resourceID int, 
                value double precision, 
                timestamp timestamp
            );"""
        )
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_lookup (
                serviceID SERIAL PRIMARY KEY,
                service_name TEXT UNIQUE NOT NULL
            );"""
        )
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_lookup (
                resourceID SERIAL PRIMARY KEY,
                resource_name TEXT UNIQUE NOT NULL
            );"""
        )

    """
        Given the name of a service/resource, return their respective ID
        If this service/resource isnt already in the database, we first insert it and give it an ID and then return it
    """
    def get_ID_from_name(self, table, row1, row2, name):
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {row1} FROM {table} WHERE {row2} = '{name}'"
            )
            result = cursor.fetchone()
            if result is None:
                cursor.execute(
                    f"INSERT INTO {table} ({row2}) VALUES ('{name}')"
                )
                self.connection.commit()
                return cursor.lastrowid
            else:
                return result[0]

    """
        Insert a row in the given table
        The timestamp is the time of insertion by default, but it can be changed to be sent by the kafka producer
    """
    def insert_metric(self, table, taskID, service_name, resource_name, value, ts=None):
        if ts is None:
            ts = datetime.datetime.utcnow().replace(microsecond=0)
        # First get the service and resource IDs from their names
        serviceID = self.get_ID_from_name("service_lookup", "serviceID", "service_name", service_name)
        resourceID = self.get_ID_from_name("resource_lookup", "resourceID", "resource_name", resource_name)
        # Then insert the IDs in the table (NOT the names)
        self.cursor.execute("INSERT INTO {table} (taskID, serviceID, resourceID, value, timestamp) VALUES (%s, %s, %s, %s, %s)"
                            .format(table=table), (taskID, serviceID, resourceID, value, ts))
        self.connection.commit()
    
    """
        Drop the specified table
    """
    def drop_table(self, table):
        self.cursor.execute("DROP TABLE {table};".format(table=table))
        self.connection.commit()
        print(f"Dropped table {table}")

    """
        Return all rows in the given table, for the specified service-resource pair
    """
    def get_data(self, table, service_name, resource_name):
        serviceID = self.get_ID_from_name("service_lookup", "serviceID", "service_name", service_name)
        resourceID = self.get_ID_from_name("resource_lookup", "resourceID", "resource_name", resource_name)
        self.cursor.execute("SELECT * FROM {table} WHERE resourceID = '{resourceID}' AND serviceID = '{serviceID}'"
                            .format(table=table, resourceID=resourceID, serviceID=serviceID))
        rows = self.cursor.fetchall()
        return rows

    """
        Returns all the rows where the data was stored between the current hour, and timedelta(hours=hour, minutes=minutes) in the future
        Not sure if we will need to inspect data based on time of day, but here it is if needed
    """
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
        Given a list of services, return the rows where the exact services in the list have been applied to the same single image
        The rows are grouped by images
    """
    def get_data_by_service_group(self, list_of_services):
        list_of_service_IDs = ()
        for name in list_of_services:
            list_of_service_IDs += (self.get_ID_from_name("service_lookup", "serviceID", "service_name", name),)
        self.cursor.execute(
            "SELECT m1.taskID, m1.serviceID, m1.resourceID, m1.value, m1.timestamp "
            "FROM metrics m1 "
            "WHERE m1.serviceID IN %s "
            "AND NOT EXISTS ( "
            "    SELECT 1 "
            "    FROM metrics m2 "
            "    WHERE m2.taskID = m1.taskID "
            "    AND m2.serviceID NOT IN %s "
            ") "
            "AND ( "
            "    SELECT COUNT(DISTINCT m3.serviceID) "
            "    FROM metrics m3 "
            "    WHERE m3.taskID = m1.taskID "
            "    AND m3.serviceID IN %s "
            ") = %s "
            "GROUP BY m1.taskID, m1.serviceID, m1.resourceID, m1.value, m1.timestamp;",
            (list_of_service_IDs, list_of_service_IDs, list_of_service_IDs, len(list_of_services))
        )
        rows = self.cursor.fetchall()
        return rows

    """
        Return all the rows in a given table
    """
    def get_historical_data(self, table):
        self.cursor.execute("SELECT * FROM {table}".format(table=table))
        rows = self.cursor.fetchall()
        return rows
    
    """
        Connection to the server needs to be close
    """
    def close_connection(self):
        self.cursor.close()
        self.connection.close()