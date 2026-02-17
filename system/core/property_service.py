from core.database import (
    get_all_cities, add_city, get_all_buildings, add_building,
    get_all_apartments, add_apartment
)

def fetch_cities():
    """Returns list of (id, name) tuples."""
    return get_all_cities()

def fetch_buildings():
    """Returns list of (b_id, c_id, street, postcode) tuples."""
    return get_all_buildings()

def fetch_apartments():
    """Returns all apartment records."""
    return get_all_apartments()

def create_city(name: str):
    if not name.strip():
        raise ValueError("City name cannot be empty.")
    add_city(name.strip())

def create_building(city_id: int, street: str, postcode: str):
    if not (street.strip() and postcode.strip()):
        raise ValueError("Street and postcode are required.")
    add_building(city_id, street.strip(), postcode.strip())

def create_apartment(city_id: int, building_id: int, num_rooms: int, apt_type: str, occupancy: str):
    if not (num_rooms and apt_type and occupancy):
        raise ValueError("All apartment fields are required.")
    add_apartment(city_id, building_id, int(num_rooms), apt_type, occupancy)

def build_city_map(cities):
    """Returns {name: id} dict from cities list."""
    return {name: c_id for c_id, name in cities}

def build_buildings_by_city(buildings):

    buildings_by_city = {}
    display_to_id = {}
    for b_id, c_id, street, postcode in buildings:
        display = f"{street} ({postcode})"
        buildings_by_city.setdefault(c_id, []).append((b_id, display))
        display_to_id[display] = b_id
    return buildings_by_city, display_to_id