import sqlite3


def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection



if __name__ == "__main__":
    connection = get_db_connection()

    with open("schema.sql") as file:
        connection.executescript(file.read())

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(users)")
    }

    if "currency" not in columns:
        connection.execute("""
            ALTER TABLE users
            ADD COLUMN currency TEXT NOT NULL DEFAULT 'INR'
            CHECK (currency IN (
                'INR', 'USD', 'GBP', 'EUR',
                'JPY', 'KRW', 'AUD', 'CAD'
            ))
        """)
        connection.commit()

    connection.close()
