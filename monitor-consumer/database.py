import datetime
import psycopg2
import psycopg2.pool
from datetime import timedelta

class Database():
    """
        The postgreSQL server is run inside the kubernetes cluster as a service
        The table metrics (orderID, taskID, resourceID, value, timestamp) is used to store the information from the messages from the producer
        Since neural networks work with numbers and not strings, we assign each task and resource an ID
        The IDs are assigned incrementally for each new task/resource in the task_lookup/resource_lookup databases by order of 10
        We do it by order of 10 so that the input we feed to the neural network isnt too similar
    """
    def __init__(self, host, port, dbname, user, password):
        pool = psycopg2.pool.SimpleConnectionPool(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            minconn=1,
            maxconn=1  # set maxconn to 1 to disable pooling
        )
        self.connection = pool.getconn()
        pool.putconn(self.connection)
        self.cursor = self.connection.cursor()
        # create main table called 'metrics'
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                orderID int, 
                taskID int, 
                resourceID int, 
                value double precision, 
                timestamp timestamp
            );"""
        )
        # create the lookup tables for the ID-name pairs
        self.cursor.execute("""
            CREATE SEQUENCE IF NOT EXISTS task_id_sequence INCREMENT BY 10 START 10;
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_lookup (
                taskID INTEGER PRIMARY KEY DEFAULT nextval('task_id_sequence'),
                task_name TEXT UNIQUE NOT NULL
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
        table, row1, row2 = "", "", ""
        if type == 0: table, row1, row2 = "task_lookup", "taskID", "task_name"
        else: table, row1, row2 = "resource_lookup", "resourceID", "resource_name"
        with self.connection.cursor() as cursor:
            # Start a database transaction
            with self.connection:
                # check if this task/resource has already been assigned an ID
                cursor.execute(
                    f"SELECT {row1} FROM {table} WHERE {row2} = '{name}' FOR UPDATE"
                )
                result = cursor.fetchone()
                if result is None:
                    # if not, we insert the task/resource in the lookup table (giving it an ID)
                    cursor.execute(
                        f"INSERT INTO {table} ({row2}) VALUES ('{name}') RETURNING {row1}"
                    )
                    self.connection.commit()
                    # and then retrieve the newly created ID
                    result = cursor.fetchone()
                    return result[0]
                else:
                    return result[0]
    
    def get_name_from_ID(self, type, ID):
        """        
            Get the name of a task/resource given its ID

            Args:
                type (int): 0 for task, 1 for resource
                ID (int): ID of the task/resource
            
            Returns:
                str: the name of the given task/resource ID
        """
        if type == 0: self.cursor.execute(f"SELECT task_name FROM task_lookup WHERE taskID = '{ID}'")
        else: self.cursor.execute(f"SELECT resource_name FROM resource_lookup WHERE resourceID = '{ID}'")
        result = self.cursor.fetchone()
        return result

    def insert_metric(self, orderID, task_name, resource_name, value, ts=None):
        """        
            Insert a row in the table metrics

            Args:
                orderID (int): ID of the order
                task_name (str): name of the task
                resource_name (str): name of the resource
                value (float): value representing the resource consumption
                ts (datetime): timestamp is the time of insertion by default, but it can be changed to be sent by the kafka producer
        """
        if ts is None:
            ts = datetime.datetime.utcnow().replace(microsecond=0)
        # First get the task and resource IDs from their names
        taskID = self.get_ID_from_name(0, task_name)
        resourceID = self.get_ID_from_name(1, resource_name)
        # Then insert the IDs in the table (NOT the names)
        self.cursor.execute("INSERT INTO metrics (orderID, taskID, resourceID, value, timestamp) VALUES (%s, %s, %s, %s, %s)", 
                            (orderID, taskID, resourceID, value, ts))
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

    def get_data(self, task_name, resource_name):
        """
            Get data based on a task-resource pair

            Args:
                task_name (str): name of the task
                resource_name (str): name of the resource

            Returns:
                [(int, int, int, float, datetime)]: all rows in the given table, for the specified task-resource pair
        """
        # get the task and resource IDs
        taskID = self.get_ID_from_name("task_lookup", "taskID", "task_name", task_name)
        resourceID = self.get_ID_from_name("resource_lookup", "resourceID", "resource_name", resource_name)
        # look them up using the IDs, not the names
        self.cursor.execute(f"SELECT * FROM metrics WHERE resourceID = '{resourceID}' AND taskID = '{taskID}'")
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
            print(f"No data found for the next {hour} hours and {minutes} minutes. No task is usually running in this timeslot.")
        return rows

    def get_data_by_task_group(self, list_of_tasks):
        """
            An order (group of tasks) will be applied to images
            Given a list of tasks, we might want the rows where the exact tasks in the list have been applied in the same order

            Args:
                list_of_tasks ([str]): list of names of tasks

            Returns:
                [(int, int, int, float, datetime)]: all rows where the exact tasks in list_of_tasks have been applied to the same single order, grouped by orderID
        
        """
        # we get the ID of each task in the list, we can use the names
        list_of_task_IDs = ()
        for name in list_of_tasks:
            list_of_task_IDs += (self.get_ID_from_name(0, name),)
        self.cursor.execute(
            "SELECT m1.orderID, m1.taskID, m1.resourceID, m1.value, m1.timestamp "
            "FROM metrics m1 "
            "WHERE m1.taskID IN %s "
            "AND NOT EXISTS ( "
            "    SELECT 1 "
            "    FROM metrics m2 "
            "    WHERE m2.orderID = m1.orderID "
            "    AND m2.taskID NOT IN %s "
            ") "
            "AND ( "
            "    SELECT COUNT(DISTINCT m3.taskID) "
            "    FROM metrics m3 "
            "    WHERE m3.orderID = m1.orderID "
            "    AND m3.taskID IN %s "
            ") = %s "
            "GROUP BY m1.orderID, m1.taskID, m1.resourceID, m1.value, m1.timestamp;",
            (list_of_task_IDs, list_of_task_IDs, list_of_task_IDs, len(list_of_tasks))
        )
        rows = self.cursor.fetchall()
        if not rows: print("No data found for this group of tasks")
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