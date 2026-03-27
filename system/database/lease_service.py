import sqlite3
from database.databaseConnection import check_connection, fetch_all, insert

def fetch_tenants(city_id=None, tenant_id=None):
    """
    Fetch tenants with optional filters.
    - city_id: Now handles city name strings (e.g., 'Bristol' or 'System')
    """
    query = """
        SELECT t.tenant_id, u.first_name || ' ' || u.surname as name, l.city_name
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
        LEFT JOIN Location l ON u.city_id = l.city_id
        WHERE 1=1
    """
    params = []
    # If city_id is 'System', we don't add the WHERE clause (show all)
    if city_id is not None and city_id != "System":
        query += " AND l.city_name = ?"
        params.append(city_id)
        
    if tenant_id is not None:
        query += " AND t.tenant_id = ?"
        params.append(tenant_id)
    
    print(f"DEBUG: fetch_tenants - city_name={city_id}")
    return fetch_all(query, params)

def fetch_available_apartments(city_id=None):
    """
    Fetch available apartments. Matches schema columns: 'occupancy_status' and 'type'.
    """
    query = """
        SELECT a.apartment_id,
               b.street || ' (' || b.postcode || ') - ' || a.type as apartment_display,
               l.city_name
        FROM Apartments a
        JOIN Buildings b ON a.building_id = b.building_id
        LEFT JOIN Location l ON b.city_id = l.city_id
        WHERE a.occupancy_status = 'Vacant'
    """
    params = []
    if city_id is not None and city_id != "System":
        query += " AND l.city_name = ?"
        params.append(city_id)
    
    print(f"DEBUG: fetch_available_apartments - city_name={city_id}")
    return fetch_all(query, params)

def fetch_leases(city_id=None, tenant_id=None):
    """
    Fetch leases. Matches schema column 'Agreed_rent'.
    """
    query = """
        SELECT 
            l.lease_id, 
            u.first_name || ' ' || u.surname as tenant_name,
            b.street || ' (' || a.type || ')' as apartment_info,
            l.start_date, 
            l.end_date, 
            l.Agreed_rent,
            loc.city_name,
            CASE 
                WHEN l.early_termination_fee > 0 THEN 'Terminated'
                WHEN date(l.end_date) < date('now') THEN 'Expired'
                ELSE 'Active'
            END as status
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        LEFT JOIN Location loc ON b.city_id = loc.city_id
        WHERE 1=1
    """
    params = []
    if city_id is not None and city_id != "System":
        query += " AND loc.city_name = ?"
        params.append(city_id)
        
    if tenant_id is not None:
        query += " AND t.tenant_id = ?"
        params.append(tenant_id)
        
    query += " ORDER BY l.start_date DESC"
    
    print(f"DEBUG: fetch_leases - city_name={city_id}")
    return fetch_all(query, params)

def build_apartment_map(apartments, **kwargs):
    """Converts apartment list into a display dictionary."""
    return {apt[1]: apt[0] for apt in apartments}

def build_tenant_map(tenants):
    """Maps tenant_name to the full tenant row."""
    return {t[1]: t for t in tenants}

# ================= LEASES =================

def create_lease(apartment_id, tenant_id, start_date, end_date, agreed_rent):
    """Inserts a new lease record including required schema fields."""
    if not all([apartment_id, tenant_id, start_date, end_date, agreed_rent]):
        raise ValueError("All lease fields are required.")

    try:
        agreed_rent = float(agreed_rent)
        deposit = agreed_rent * 1.5 # Default deposit logic
    except:
        raise ValueError("Rent must be a number.")

    insert(
        """
        INSERT INTO Lease (
            apartment_id, tenant_id, start_date, end_date, Agreed_rent, early_termination_fee, deposit
        ) VALUES (?, ?, ?, ?, ?, 0, ?)
        """,
        (apartment_id, tenant_id, start_date, end_date, agreed_rent, deposit)
    )

# ================= TERMINATION & UTIL =================

def update_lease_early_termination(lease_id, fee):
    """Updates termination fee for a specific lease."""
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Lease SET early_termination_fee = ? WHERE lease_id = ?", (fee, lease_id))
    conn.commit()
    conn.close()