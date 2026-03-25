from config.db import get_connection
from mysql.connector import Error


def fetch_all_from_table(table_name):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        return records
    except Error as e:
        print(f"Error executing query: {e}")
        return []
    finally:
        cursor.close()
