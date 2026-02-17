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



def get_all_cities():
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city_id, city_name FROM Location")
    cities = cursor.fetchall()
    conn.close()
    return cities

def add_city(city_name):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Location (city_name) VALUES (?)", (city_name,))
    conn.commit()
    conn.close()

# -------------------- Buildings --------------------
def get_all_buildings():
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT building_id, city_id, street, postcode FROM Buildings")
    buildings = cursor.fetchall()
    conn.close()
    return buildings

def add_building(city_id, street, postcode):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Buildings (city_id, street, postcode) VALUES (?, ?, ?)",
        (city_id, street, postcode)
    )
    conn.commit()
    conn.close()

# -------------------- Apartments --------------------
def get_all_apartments():
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.apartment_id, l.city_name, b.street, b.postcode, a.num_rooms, a.type, a.occupancy_status
        FROM Apartments a
        JOIN Location l ON a.city_id = l.city_id
        JOIN Buildings b ON a.building_id = b.building_id
    """)
    apartments = cursor.fetchall()
    conn.close()
    return apartments

def add_apartment(city_id, building_id, num_rooms, apt_type, occupancy_status):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Apartments (city_id, building_id, num_rooms, type, occupancy_status) VALUES (?, ?, ?, ?, ?)",
        (city_id, building_id, num_rooms, apt_type, occupancy_status)
    )
    conn.commit()
    conn.close()