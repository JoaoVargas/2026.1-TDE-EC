import mysql.connector
from mysql.connector import Error

_connection = None


def get_connection():
    global _connection
    if _connection is None or not _connection.is_connected():
        try:
            _connection = mysql.connector.connect(
                host="localhost",
                user="user",
                password="password",
                database="mydb",
            )
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            _connection = None
    return _connection
