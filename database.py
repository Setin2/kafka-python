import psycopg2
import datetime

class Database():
    def __init__(self):
        self.connection = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password="postgres"
        )
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS metrics (service varchar(255), resource varchar(255), value double precision, timestamp timestamp)")

    def insert_metric(self, service, resource, value):
        ts = datetime.datetime.utcnow().replace(microsecond=0)
        self.cursor.execute("INSERT INTO metrics (service, resource, value, timestamp) VALUES (%s, %s, %s, %s)", (service, resource, value, ts))
        self.connection.commit()
    
    def drop_table(self):
        self.cursor.execute("DROP TABLE IF EXISTS metrics")

    def get_data(self, service, resource):
        self.cursor.execute("SELECT * FROM metrics WHERE resource = '{resource}' AND service = '{service}'"
                            .format(resource=resource, service=service))
        rows = self.cursor.fetchall()
        return rows
    
    def close_connection(self):
        self.cursor.close()
        self.connection.close()