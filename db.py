import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port=4444,
        database="testbaby",
        user="postgres",
        password="french4477"
    )
