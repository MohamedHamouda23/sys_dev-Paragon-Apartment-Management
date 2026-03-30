from database.databaseConnection import fetch_all, insert
from .db_utils import execute_query

# ============================================================================
# CITIES
# ============================================================================

def get_all_cities(scope_city_id=None):
    if scope_city_id is None:
        return fetch_all("SELECT city_id, city_name FROM Location ORDER BY city_name")
    
    return execute_query(
        "SELECT city_id, city_name FROM Location WHERE city_id = ? ORDER BY city_name",
        (scope_city_id,)
    )


def create_city(city_name):
    insert("INSERT INTO Location (city_name) VALUES (?)", (city_name,))


def build_city_map(cities=None):
    if cities is None:
        cities = get_all_cities()
    return {city_name: city_id for city_id, city_name in cities}


# ============================================================================
# BUILDINGS
# ============================================================================

def get_all_buildings(scope_city_id=None):
    if scope_city_id is None:
        return fetch_all("SELECT building_id, city_id, street, postcode FROM Buildings")
    
    return execute_query(
        "SELECT building_id, city_id, street, postcode FROM Buildings WHERE city_id = ?",
        (scope_city_id,)
    )


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


# ============================================================================
# APARTMENTS
# ============================================================================

def get_all_apartments(scope_city_id=None):
    query = """
        SELECT a.apartment_id, l.city_name, b.street, b.postcode, a.num_rooms, a.type, a.occupancy_status
        FROM Apartments a
        JOIN Location l ON a.city_id = l.city_id
        JOIN Buildings b ON a.building_id = b.building_id
    """
    
    if scope_city_id is None:
        return fetch_all(query)
    
    return execute_query(query + " WHERE a.city_id = ?", (scope_city_id,))


def create_apartment(city_id, building_id, num_rooms, apt_type, occupancy_status):
    insert(
        "INSERT INTO Apartments (city_id, building_id, num_rooms, type, occupancy_status) VALUES (?, ?, ?, ?, ?)",
        (city_id, building_id, num_rooms, apt_type, occupancy_status)
    )


def get_apartments_by_status(status, scope_city_id=None):
    query = """
        SELECT a.apartment_id, l.city_name, b.street, b.postcode, a.num_rooms, a.type, a.occupancy_status
        FROM Apartments a
        JOIN Location l ON a.city_id = l.city_id
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE a.occupancy_status = ?
    """
    params = [status]

    if scope_city_id is not None:
        query += " AND a.city_id = ?"
        params.append(scope_city_id)

    query += " ORDER BY a.apartment_id"
    return execute_query(query, tuple(params))


def update_apartment_status(apartment_id, new_status):
    allowed = {"Vacant", "Unavailable"}
    if new_status not in allowed:
        raise ValueError("Invalid occupancy status. Only Vacant or Unavailable can be set manually.")

    current = execute_query(
        "SELECT occupancy_status FROM Apartments WHERE apartment_id = ?",
        (apartment_id,),
        'one'
    )
    if not current:
        raise ValueError("Apartment not found.")
    if str(current[0]).strip() == "Occupied":
        raise ValueError("Occupied apartments cannot be changed manually.")

    execute_query(
        "UPDATE Apartments SET occupancy_status = ? WHERE apartment_id = ?",
        (new_status, apartment_id),
        'none'
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