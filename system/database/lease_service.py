from database.databaseConnection import check_connection, fetch_all, insert

# ================= TENANTS =================

def fetch_tenants(city_id=None):
    query = """
        SELECT t.tenant_id, u.first_name || ' ' || u.surname
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
        WHERE 1=1
    """
    params = []

    if city_id is not None:
        query += " AND u.city_id = ?"
        params.append(city_id)

    return fetch_all(query, tuple(params))


def build_tenant_map(tenants):
    return {name: t_id for t_id, name in tenants}



# ================= APARTMENTS =================

def fetch_available_apartments(city_id=None):
    query = """
        SELECT
            a.apartment_id,
            b.street || ' (' || b.postcode || ') - ' || a.type,
            a.city_id
        FROM Apartments a
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE a.occupancy_status = 'Vacant'
    """
    params = []

    if city_id is not None:
        query += " AND a.city_id = ?"
        params.append(city_id)

    return fetch_all(query, tuple(params))


def build_apartment_map(apartments, city_id=None):
    result = {}
    for apt in apartments:
        apt_id = apt[0]
        display = apt[1]
        apt_city_id = apt[2] if len(apt) > 2 else None

        if city_id is not None and apt_city_id != city_id:
            continue

        result[display] = apt_id
    return result


# ================= LEASES =================

def fetch_leases(city_id=None, tenant_id=None):
    """
    Returns rows in THIS exact order:
    (
        lease_id,
        tenant_name,
        apartment_display,
        start_date,
        end_date,
        agreed_rent,
        city_name,
        status
    )
    """
    query = """
        SELECT
            l.lease_id,
            u.first_name || ' ' || u.surname AS tenant_name,
            a.type || ' - ' || b.street || ', ' || b.postcode AS apartment_display,
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            loc.city_name,
            CASE
                WHEN COALESCE(l.early_termination_fee, 0) > 0 THEN 'Terminated'
                WHEN DATE(l.end_date) < DATE('now') THEN 'Expired'
                ELSE 'Active'
            END AS status
        FROM Lease l
        JOIN Tenant t     ON l.tenant_id = t.tenant_id
        JOIN User u       ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b  ON a.building_id = b.building_id
        JOIN Location loc ON a.city_id = loc.city_id
        WHERE 1=1
    """
    params = []

    if city_id is not None:
        query += " AND a.city_id = ?"
        params.append(city_id)

    if tenant_id is not None:
        query += " AND l.tenant_id = ?"
        params.append(tenant_id)

    query += """
        ORDER BY
            CASE
                WHEN COALESCE(l.early_termination_fee, 0) > 0 THEN 2
                WHEN DATE(l.end_date) < DATE('now') THEN 1
                ELSE 0
            END,
            DATE(l.end_date) DESC
    """

    return fetch_all(query, tuple(params))

def create_lease(apartment_id, tenant_id, start_date, end_date, agreed_rent):
    # prevent empty values
    if (
        apartment_id in (None, "")
        or tenant_id in (None, "")
        or not str(start_date).strip()
        or not str(end_date).strip()
        or not str(agreed_rent).strip()
    ):
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
            apartment_id,
            tenant_id,
            start_date,
            end_date,
            Agreed_rent,
            early_termination_fee
        ) VALUES (?, ?, ?, ?, ?, 0)
        """,
        (apartment_id, tenant_id, start_date, end_date, agreed_rent)
    )


# ================= UPDATE / TERMINATION =================

def update_lease(lease_id, start_date, end_date, agreed_rent):
    if lease_id in (None, ""):
        raise ValueError("Lease ID is required.")

    if not str(start_date).strip() or not str(end_date).strip() or not str(agreed_rent).strip():
        raise ValueError("All update fields are required.")

    try:
        agreed_rent = float(agreed_rent)
    except Exception:
        raise ValueError("Rent must be a number.")

    if agreed_rent <= 0:
        raise ValueError("Rent must be greater than 0.")

    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Lease
        SET start_date = ?, end_date = ?, Agreed_rent = ?
        WHERE lease_id = ?
        """,
        (start_date, end_date, agreed_rent, lease_id)
    )
    conn.commit()
    conn.close()


def update_lease_early_termination(lease_id, fee):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Lease SET early_termination_fee = ? WHERE lease_id = ?",
        (fee, lease_id)
    )
    conn.commit()
    conn.close()
