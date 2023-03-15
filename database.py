import datetime
import psycopg2
import psycopg2.pool
from datetime import timedelta

class Database():
    """
        The postgreSQL server is run in docker
        The table metrics (tastID, serviceID, resourceID, value, timestamp) is used to store the information from the messages from the producer
        Since neural networks work with numbers and not strings, we assign each service and resource an ID
        The IDs are assigned incrementally for each new service/resource in the service_lookup/resource_lookup databases by order of 10
        We do it by order of 10 so that the input we feed to the neural network isnt too similar
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
        # create main table called 'metrics'
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                taskID int, 
                serviceID int, 
                resourceID int, 
                value double precision, 
                timestamp timestamp
            );"""
        )
        # create the lookup tables for the ID-name pairs
        self.cursor.execute("""
            CREATE SEQUENCE IF NOT EXISTS service_id_sequence INCREMENT BY 10 START 10;
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_lookup (
                serviceID INTEGER PRIMARY KEY DEFAULT nextval('service_id_sequence'),
                service_name TEXT UNIQUE NOT NULL
            );"""
        )
        self.cursor.execute("""
            CREATE SEQUENCE IF NOT EXISTS resource_id_sequence INCREMENT BY 10 START 10;
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_lookup (
                resourceID INTEGER PRIMARY KEY DEFAULT nextval('resource_id_sequence'),
                resource_name TEXT UNIQUE NOT NULL
            );"""
        )
    
    def get_ID_from_name(self, type, name):
        """        
            Get the ID of a service/resource given its name

            Args:
                type (int): 0 for service, 1 for resource
                name (str): name of the service/resource
            
            Returns:
                int: the ID of the given service/resource
        """
        table, row1, row2 = "", "", ""
        if type == 0: table, row1, row2 = "service_lookup", "serviceID", "service_name"
        else: table, row1, row2 = "resource_lookup", "resourceID", "resource_name"
        with self.connection.cursor() as cursor:
            # check if this service/resource has already been assigned an ID
            cursor.execute(
                f"SELECT {row1} FROM {table} WHERE {row2} = '{name}'"
            )
            result = cursor.fetchone()
            if result is None:
                # if not, we insert the service/resource in the lookup table (giving it an ID)
                cursor.execute(
                    f"INSERT INTO {table} ({row2}) VALUES ('{name}')"
                )
                self.connection.commit()
                # and then retrieve the newly created ID
                cursor.execute(
                    f"SELECT {row1} FROM {table} ORDER BY {row1} DESC LIMIT 1"
                )
                result = self.cursor.fetchone()
                return result
            else:
                return result[0]
    
    def get_name_from_ID(self, type, ID):
        """        
            Get the name of a service/resource given its ID

            Args:
                type (int): 0 for service, 1 for resource
                ID (int): ID of the service/resource
            
            Returns:
                str: the name of the given service/resource ID
        """
        if type == 0: self.cursor.execute(f"SELECT service_name FROM service_lookup WHERE serviceID = '{ID}'")
        else: self.cursor.execute(f"SELECT resource_name FROM resource_lookup WHERE resourceID = '{ID}'")
        result = self.cursor.fetchone()
        return result

    def insert_metric(self, taskID, service_name, resource_name, value, ts=None):
        """        
            Insert a row in the given table

            Args:
                taskID (int): ID of the task
                service_name (str): name of the service
                resource_name (str): name of the resource
                value (float): value representing the resource consumption
                ts (datetime): timestamp is the time of insertion by default, but it can be changed to be sent by the kafka producer
        """
        if ts is None:
            ts = datetime.datetime.utcnow().replace(microsecond=0)
        # First get the service and resource IDs from their names
        serviceID = self.get_ID_from_name(0, service_name)
        resourceID = self.get_ID_from_name(1, resource_name)
        # Then insert the IDs in the table (NOT the names)
        self.cursor.execute("INSERT INTO metrics (taskID, serviceID, resourceID, value, timestamp) VALUES (%s, %s, %s, %s, %s)", 
                            (taskID, serviceID, resourceID, value, ts))
        self.connection.commit()
    
    def drop_table(self, table):
        """
            Drop the specified table

            Args:
                table (str): name of the table we wish to drop
        """
        self.cursor.execute("DROP TABLE {table};".format(table=table))
        self.connection.commit()
        print(f"Dropped table {table}")

    def get_data(self, service_name, resource_name):
        """
            Get data based on a service-resource pair

            Args:
                service_name (str): name of the service
                resource_name (str): name of the resource

            Returns:
                [(int, int, int, float, datetime)]: all rows in the given table, for the specified service-resource pair
        """
        # get the service and resource IDs
        serviceID = self.get_ID_from_name("service_lookup", "serviceID", "service_name", service_name)
        resourceID = self.get_ID_from_name("resource_lookup", "resourceID", "resource_name", resource_name)
        # look them up using the IDs, not the names
        self.cursor.execute(f"SELECT * FROM metrics WHERE resourceID = '{resourceID}' AND serviceID = '{serviceID}'")
        rows = self.cursor.fetchall()
        return rows

    def get_data_for_next_x_hours(self, hour, minutes):
        """
            Get data that was stored between the current time of the day, and timedelta(hours=hour, minutes=minutes) in the future.
            Not sure if we will need to inspect data based on time of day, but here it is if needed.

            Args:
                hour (int): number of hours
                minutes (int): number of minutes

            Returns:
                [(int, int, int, float, datetime)]: all rows in the given table, given the desired timeslot
        """
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        ts_plus = ts + timedelta(hours=hour, minutes=minutes)
        self.cursor.execute("SELECT * FROM metrics WHERE timestamp >= %s AND timestamp <= %s", (ts, ts_plus))
        rows = self.cursor.fetchall()
        if not rows:
            print(f"No data found for the next {hour} hours and {minutes} minutes. No service is usually running in this timeslot.")
        return rows

    def get_data_by_service_group(self, list_of_services):
        """
            A task (group of services) will be applied to an image
            Given a list of services, we might want the rows where the exact services in the list have been applied to the same single image

            Args:
                list_of_services ([str]): list of names of services

            Returns:
                [(int, int, int, float, datetime)]: all rows where the exact services in list_of_services have been applied to the same single task, grouped by taskID
        
        """
        # we get the ID of each service in the list, we can use the names
        list_of_service_IDs = ()
        for name in list_of_services:
            list_of_service_IDs += (self.get_ID_from_name(0, name),)
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
        if not rows: print("No data found for this group of services")
        return rows

    def get_historical_data(self, table):
        """
            Get all the rows in a given table

            Args:
                table (str): name of the table

            Returns:
                [(int, int, int, float, datetime)]: all the rows in a given table
        """
        self.cursor.execute("SELECT * FROM {table}".format(table=table))
        rows = self.cursor.fetchall()
        return rows
    
    def delete_row(self, table, row, value):
        """
            Delete every row of this name with this value

            Args:
                table (str): name of the table we wish to delete from
                row (str): name of the row
                value (int/float/datetime): value of the rows we wish to delete
        """

        self.cursor.execute(f"DELETE FROM {table} WHERE {row}={value}")
        self.connection.commit()
        print(f"All rows where {row}={value} have been deleted")
    
    def close_connection(self):
        """
            Connection to the server needs to be closed
        """
        self.cursor.close()
        self.connection.close()
        print("Connection to the database closed.")