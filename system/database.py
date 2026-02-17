import sqlite3

def check_connection(db_path="database/database.db"):
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print("Connection failed:", e)
        return None


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


def get_cities():
    # Fetch cities from DB
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city_id, city_name FROM Location")
    cities = cursor.fetchall()
    city_names = [c[1] for c in cities]
    city_ids = {c[1]: c[0] for c in cities}

    # Fetch all buildings and organize by city_id, include postcode
    cursor.execute("SELECT building_id, city_id, street, postcode FROM Buildings")
    buildings = cursor.fetchall()
    buildings_by_city = {}
    display_to_id = {}
    for b_id, c_id, street, postcode in buildings:
        display = f"{street} ({postcode})"
        buildings_by_city.setdefault(c_id, []).append((b_id, display))
        display_to_id[display] = b_id
    conn.close()
    return city_names, city_ids, buildings_by_city, display_to_id


def get_all_apartments():
    try:
        conn = check_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.apartment_id, l.city_name, b.street, b.postcode, a.num_rooms, a.type, a.occupancy_status
            FROM Apartments a
            JOIN Location l ON a.city_id = l.city_id
            JOIN Buildings b ON a.building_id = b.building_id
        """)
        apartments = cursor.fetchall()
        return apartments
    finally:
        conn.close()


def add_city(city_name):
    try:
        conn = check_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Location (city_name) VALUES (?)",
            (city_name,)
        )
        conn.commit()
    except Exception as e:
        print(f"Error adding city: {e}")
        raise
    finally:
        conn.close()
