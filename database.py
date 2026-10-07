import sqlite3


def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


if __name__ == "__main__":
    connection = get_db_connection()

    with open("schema.sql") as file:
        connection.executescript(file.read())

    connection.close()