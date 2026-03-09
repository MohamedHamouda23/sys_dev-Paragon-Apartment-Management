import sqlite3
def check_connection(db_path="database/database.db"):
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print("Connection failed:", e)
        return None



# -------------------- Generic Helpers --------------------
def fetch_all(query):
    """Fetch all rows from a query."""
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return result

def insert(query, params):
    """Insert data into the database."""
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()
