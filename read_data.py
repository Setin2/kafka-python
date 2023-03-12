import psycopg2

# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="postgres",
    user="postgres",
    password="postgres"
)

# Open a cursor to perform database operations
cursor = conn.cursor()

# Execute a SELECT statement to retrieve data from a table
#cursor.execute('SELECT * FROM metrics')
cursor.execute("SELECT * FROM metrics WHERE resource = 'CPU'")

# Fetch all rows and print the results
rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the cursor and database connection
cursor.close()
conn.close()
