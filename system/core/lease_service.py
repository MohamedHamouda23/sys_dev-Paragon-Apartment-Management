from core.database import (
    get_all_leases,
    add_lease,
    get_all_apartments,
)

def fetch_leases():
    """Returns all lease records."""
    return get_all_leases()


def fetch_tenants():
    """Returns list of (tenant_id, full_name) tuples."""
    from core.database import check_connection

    conn = check_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.tenant_id, u.first_name || ' ' || u.surname
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
    """)

    tenants = cursor.fetchall()
    conn.close()
    return tenants

def fetch_available_apartments():
    """Returns only Vacant apartments as (apartment_id, display_str) tuples."""
    apartments = get_all_apartments()
    # get_all_apartments returns:
    # (apartment_id, city_name, street, postcode, num_rooms, type, occupancy_status)
    return [
        (apt[0], f"{apt[2]} ({apt[3]}) – {apt[5]}")
        for apt in apartments
        if apt[6] == "Vacant"
    ]


def build_tenant_map(tenants):
    """Returns {full_name: tenant_id} dict."""
    return {name: t_id for t_id, name in tenants}


def build_apartment_map(apartments):
    """Returns {display_str: apartment_id} dict."""
    return {display: apt_id for apt_id, display in apartments}



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