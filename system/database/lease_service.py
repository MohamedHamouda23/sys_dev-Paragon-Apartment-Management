from database.databaseConnection import check_connection, fetch_all, insert

# ================= TENANTS =================

def fetch_tenants():
    return fetch_all("""
        SELECT t.tenant_id, u.first_name || ' ' || u.surname
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
    """)

def build_tenant_map(tenants):
    return {name: t_id for t_id, name in tenants}

# ================= APARTMENTS =================

def fetch_available_apartments():
    return fetch_all("""
        SELECT a.apartment_id, b.street || ' (' || b.postcode || ') - ' || a.type, a.city_id
        FROM Apartments a
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE a.occupancy_status = 'Vacant'
    """)

def build_apartment_map(apartments, city_id=None):
    """Build apartment map, optionally filtering by city"""
    result = {}
    for apt in apartments:
        apt_id = apt[0]
        display = apt[1]
        apt_city_id = apt[2] if len(apt) > 2 else None
        
        # Filter by city if specified
        if city_id is not None and apt_city_id != city_id:
            continue
        
        result[display] = apt_id
    return result

# ================= LEASES =================

def fetch_leases():
    return fetch_all("""
        SELECT
            l.lease_id,
            l.apartment_id,
            l.tenant_id,
            u.first_name || ' ' || u.surname,
            b.street || ' (' || b.postcode || ')',
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            CASE
                WHEN COALESCE(l.early_termination_fee, 0) > 0 THEN 'Terminated'
                WHEN l.end_date < DATE('now')               THEN 'Expired'
                ELSE 'Active'
            END,
            a.city_id
        FROM Lease l
        JOIN Tenant t     ON l.tenant_id    = t.tenant_id
        JOIN User u       ON t.user_id      = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b  ON a.building_id  = b.building_id
    """)

def create_lease(apartment_id, tenant_id, start_date, end_date, agreed_rent):
    if not all([apartment_id, tenant_id, start_date, end_date, agreed_rent]):
        raise ValueError("All lease fields are required.")
    try:
        agreed_rent = float(agreed_rent)
    except Exception:
        raise ValueError("Rent must be a number.")
    if agreed_rent <= 0:
        raise ValueError("Rent must be greater than 0.")
    insert(
        """
        INSERT INTO Lease (
            apartment_id, tenant_id, start_date,
            end_date, Agreed_rent, early_termination_fee
        ) VALUES (?, ?, ?, ?, ?, 0)
        """,
        (apartment_id, tenant_id, start_date, end_date, agreed_rent)
    )

# ================= TERMINATION =================

def update_lease_early_termination(lease_id, fee):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Lease SET early_termination_fee = ? WHERE lease_id = ?",
        (fee, lease_id)
    )
    conn.commit()
    conn.close()