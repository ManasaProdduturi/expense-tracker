import sqlite3


def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


if __name__ == "__main__":
    connection = get_db_connection()

    with open("schema.sql") as file:
        connection.executescript(file.read())

    # Add currency to older users tables if needed.
    user_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(users)")
    }

    if "currency" not in user_columns:
        connection.execute("""
            ALTER TABLE users
            ADD COLUMN currency TEXT NOT NULL DEFAULT 'INR'
            CHECK (currency IN (
                'INR', 'USD', 'GBP', 'EUR',
                'JPY', 'KRW', 'AUD', 'CAD'
            ))
        """)

    # Add recreation tracking to older deleted_users tables.
    deleted_user_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(deleted_users)")
    }

    if "recreated" not in deleted_user_columns:
        connection.execute("""
            ALTER TABLE deleted_users
            ADD COLUMN recreated INTEGER NOT NULL DEFAULT 0
            CHECK (recreated IN (0, 1))
        """)

    if "recreated_at" not in deleted_user_columns:
        connection.execute("""
            ALTER TABLE deleted_users
            ADD COLUMN recreated_at TEXT
        """)

    connection.commit()
    connection.close()