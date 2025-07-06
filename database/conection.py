import psycopg2
from config import POSTGRESQL_URL

def get_pg_connection():
    conn = psycopg2.connect(
        dbname=POSTGRESQL_URL['dbname'],
        user=POSTGRESQL_URL['user'],
        password=POSTGRESQL_URL['password'],
        host=POSTGRESQL_URL['host'],
        port=POSTGRESQL_URL['port']
    )
    return conn
