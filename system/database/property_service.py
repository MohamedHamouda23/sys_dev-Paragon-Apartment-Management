from database.databaseConnection import check_connection,fetch_all, insert


# -------------------- Cities --------------------
def get_all_cities():
    return fetch_all("SELECT city_id, city_name FROM Location")

def create_city(city_name):
    insert("INSERT INTO Location (city_name) VALUES (?)", (city_name,))

def build_city_map(cities=None):
    if cities is None:
        cities = get_all_cities()
    return {city_name: city_id for city_id, city_name in cities}

# -------------------- Buildings --------------------
def get_all_buildings():
    return fetch_all("SELECT building_id, city_id, street, postcode FROM Buildings")

def create_building(city_id, street, postcode):
    insert(
        "INSERT INTO Buildings (city_id, street, postcode) VALUES (?, ?, ?)",
        (city_id, street, postcode)
    )

def build_buildings_by_city(buildings=None):
    if buildings is None:
        buildings = get_all_buildings()
    buildings_by_city = {}
    display_to_id = {}
    for building_id, city_id, street, postcode in buildings:
        display = f"{street} ({postcode})"
        display_to_id[display] = building_id
        if city_id not in buildings_by_city:
            buildings_by_city[city_id] = []
        buildings_by_city[city_id].append((building_id, display))
    return buildings_by_city, display_to_id

# -------------------- Apartments --------------------
def get_all_apartments():
    return fetch_all("""
        SELECT a.apartment_id, l.city_name, b.street, b.postcode, a.num_rooms, a.type, a.occupancy_status
        FROM Apartments a
        JOIN Location l ON a.city_id = l.city_id
        JOIN Buildings b ON a.building_id = b.building_id
    """)

def create_apartment(city_id, building_id, num_rooms, apt_type, occupancy_status):
    insert(
        "INSERT INTO Apartments (city_id, building_id, num_rooms, type, occupancy_status) VALUES (?, ?, ?, ?, ?)",
        (city_id, building_id, num_rooms, apt_type, occupancy_status)
    )

def fetch_available_apartments():
    apartments = get_all_apartments()
    return [
        (apt[0], f"{apt[1]} ({apt[2]}) - {apt[4]}")
        for apt in apartments
        if apt[6] == "Vacant"
    ]

def build_apartment_map(apartments):
    """Returns {display_str: apartment_id} dict."""
    return {display: apt_id for apt_id, display in apartments}