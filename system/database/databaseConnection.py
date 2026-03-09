import sqlite3
def check_connection(db_path="database/database.db"):
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print("Connection failed:", e)
        return None

