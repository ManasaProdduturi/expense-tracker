import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()

    try:
        with open(SCHEMA_PATH, encoding="utf-8") as file:
            connection.executescript(file.read())

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
    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()