from database.databaseConnection import check_connection,fetch_all, insert



def build_tenant_map(tenants):
    """Returns {full_name: tenant_id} dict."""
    return {name: t_id for t_id, name in tenants}



def fetch_tenants():
    """Returns list of (tenant_id, full_name) tuples."""
    return fetch_all("""
        SELECT t.tenant_id, u.first_name || ' ' || u.surname
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
    """)



# -------------------- Create Lease Logic --------------------

def fetch_leases():
    """Returns all lease records."""
    return get_all_leases()


def create_lease(
    apartment_id: int,
    tenant_id: int,
    start_date: str,
    end_date: str,
    agreed_rent: float,
):
    if not (apartment_id and tenant_id and start_date and end_date and agreed_rent):
        raise ValueError("All lease fields are required.")
    try:
        agreed_rent = float(agreed_rent)
    except ValueError:
        raise ValueError("Rent must be a number.")

    if agreed_rent <= 0:
        raise ValueError("Rent must be greater than zero.")

    add_lease(int(apartment_id), int(tenant_id), start_date, end_date, agreed_rent)



def add_lease(apartment_id, tenant_id, start_date, end_date, agreed_rent):
    insert(
        """
        INSERT INTO Lease (
            apartment_id,
            tenant_id,
            start_date,
            end_date,
            Agreed_rent,
            early_termination_fee
        )
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (apartment_id, tenant_id, start_date, end_date, agreed_rent)
    )


def get_all_leases():
    return fetch_all("""
        SELECT
            l.lease_id,
            l.apartment_id,
            l.tenant_id,
            u.first_name || ' ' || u.surname AS tenant_name,
            b.street || ' (' || b.postcode || ')' AS apt_display,
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            CASE
                WHEN COALESCE(l.early_termination_fee,0) > 0 THEN 'Terminated'
                WHEN l.end_date < DATE('now') THEN 'Expired'
                ELSE 'Active'
            END AS status
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
    """)


def update_lease_early_termination(lease_id, fee):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Lease SET early_termination_fee = ? WHERE lease_id = ?",
        (fee, lease_id)
    )
    conn.commit()
    conn.close()