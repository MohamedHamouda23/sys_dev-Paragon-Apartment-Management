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



def add_apartment(city_id, building_id, num_rooms, apt_type, occ):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Apartments (city_id, building_id, num_rooms, type, occupancy_status) VALUES (?, ?, ?, ?, ?)",
        (city_id, building_id, int(num_rooms), apt_type, occ)
    )
    conn.commit()
    conn.close()
