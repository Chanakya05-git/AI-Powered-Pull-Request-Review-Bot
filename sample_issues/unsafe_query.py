import sqlite3


def find_user(database_path, name):
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
    result = cursor.fetchone()
    connection.close()
    return result