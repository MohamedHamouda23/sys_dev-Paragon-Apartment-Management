from database.databaseConnection import (
   check_connection
)


def get_all_users():
    conn = check_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.user_id,
            u.first_name,
            u.surname,
            ua.email,
            COALESCE(l.city_name, ''),
            r.role_name
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        LEFT JOIN Location l ON u.city_id = l.city_id
        JOIN Role r ON ua.role_id = r.role_id
        ORDER BY u.user_id ASC
    """)
    users = cursor.fetchall()
    conn.close()
    return users


def get_all_roles():
    conn = check_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT role_id, role_name FROM Role ORDER BY role_name ASC")
    roles = cursor.fetchall()
    conn.close()
    return roles


def get_all_locations():
    conn = check_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT city_id, city_name FROM Location ORDER BY city_name ASC")
    cities = cursor.fetchall()
    conn.close()
    return cities


def create_user(first_name, surname, email, password_hash, role_id, city_id=None):
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM User_Access WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email already exists.")

    cursor.execute(
        "INSERT INTO User (city_id, first_name, surname) VALUES (?, ?, ?)",
        (city_id, first_name, surname)
    )
    new_user_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES (?, ?, ?, ?)",
        (new_user_id, password_hash, role_id, email)
    )
    conn.commit()
    conn.close()


def update_user(user_id, first_name, surname, email, role_id, city_id=None, password_hash=None):
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM User_Access WHERE email = ? AND user_id != ?",
        (email, user_id)
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email already exists.")

    cursor.execute(
        "UPDATE User SET city_id = ?, first_name = ?, surname = ? WHERE user_id = ?",
        (city_id, first_name, surname, user_id)
    )

    if password_hash:
        cursor.execute(
            "UPDATE User_Access SET email = ?, role_id = ?, password_hash = ? WHERE user_id = ?",
            (email, role_id, password_hash, user_id)
        )
    else:
        cursor.execute(
            "UPDATE User_Access SET email = ?, role_id = ? WHERE user_id = ?",
            (email, role_id, user_id)
        )

    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    cursor = conn.cursor()
    cursor.execute("DELETE FROM User_Access WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM User WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def check_user(email, password):
       
    conn = check_connection()

    if conn is None:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1
        FROM User_Access
        WHERE email = ? AND password_hash = ?
    """, (email, password))

    user = cursor.fetchone()

    conn.close()

    return user

def retrive_data(email, password):
    
    conn = check_connection()
    if conn is None:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.user_id,
            u.first_name,
            u.surname,
            l.city_name,
            r.role_name
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        JOIN Location l ON u.city_id = l.city_id
        WHERE ua.email = ? AND ua.password_hash = ?
    """, (email, password))

    user_data = cursor.fetchone()
    conn.close()
    return user_data
