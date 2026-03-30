from database.databaseConnection import fetch_all, insert, check_connection
from .db_utils import execute_query
from validations import validate_required_fields, validate_positive_number
from datetime import date
from calendar import monthrange


def _add_months(base_date, months):
    """Add months while keeping day-of-month stable when possible."""
    year = base_date.year + ((base_date.month - 1 + months) // 12)
    month = ((base_date.month - 1 + months) % 12) + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def _monthly_due_dates(start_dt, end_dt, horizon_dt):
    """Yield monthly due dates from start to min(end, horizon)."""
    final_dt = min(end_dt, horizon_dt)
    due = start_dt
    while due <= final_dt:
        yield due
        due = _add_months(due, 1)


def sync_lease_payments_up_to_horizon(conn=None, lease_id=None, months_ahead=1):
    """Ensure monthly payment rows exist up to N months ahead for one or all leases."""
    own_conn = conn is None
    conn = conn or check_connection()
    cursor = conn.cursor()

    today = date.today()
    horizon_dt = _add_months(today, months_ahead)

    query = "SELECT lease_id, start_date, end_date FROM Lease"
    params = ()
    if lease_id is not None:
        query += " WHERE lease_id = ?"
        params = (lease_id,)

    cursor.execute(query, params)
    leases = cursor.fetchall()
    inserted_count = 0

    for l_id, start_date, end_date in leases:
        if not start_date or not end_date:
            continue

        start_dt = date.fromisoformat(str(start_date))
        end_dt = date.fromisoformat(str(end_date))
        if end_dt < start_dt:
            continue

        # Keep only near-term placeholders; do not remove paid/partial future entries.
        cursor.execute(
            """
            DELETE FROM Payment
            WHERE lease_id = ?
              AND DATE(due_date) > DATE(?)
              AND payment_date IS NULL
              AND COALESCE(amount, 0) = 0
            """,
            (l_id, horizon_dt.isoformat()),
        )

        for due_dt in _monthly_due_dates(start_dt, end_dt, horizon_dt):
            due_str = due_dt.isoformat()
            cursor.execute(
                "SELECT 1 FROM Payment WHERE lease_id = ? AND due_date = ? LIMIT 1",
                (l_id, due_str),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO Payment (lease_id, due_date, payment_date, amount, Is_late)
                    VALUES (?, ?, NULL, 0, 'No')
                    """,
                    (l_id, due_str),
                )
                inserted_count += 1

    if own_conn:
        conn.commit()
        conn.close()

    return inserted_count


# ============================================================================
# TENANTS
# ============================================================================

def fetch_tenants(city_id=None, tenant_id=None):
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

    if tenant_id is not None:
        query += " AND t.tenant_id = ?"
        params.append(tenant_id)

    return fetch_all(query, tuple(params))


def build_tenant_map(tenants):
    return {name: t_id for t_id, name in tenants}


# ============================================================================
# APARTMENTS
# ============================================================================

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


# ============================================================================
# LEASES
# ============================================================================

def fetch_leases(city_id=None, tenant_id=None):
    """
    Returns rows in THIS exact order:
    (lease_id, tenant_name, apartment_display, start_date, end_date, agreed_rent, city_name, status)
    """
    query = """
        SELECT
            l.lease_id,
            u.first_name || ' ' || u.surname AS tenant_name,
            a.type || ' - ' || b.street || ', ' || b.postcode AS apartment_display,
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            TRIM(loc.city_name) AS city_name,
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
    # Validate all fields
    validate_required_fields({
        'apartment_id': apartment_id,
        'tenant_id': tenant_id,
        'start_date': start_date,
        'end_date': end_date,
        'agreed_rent': agreed_rent
    })

    # Validate rent is a positive number
    agreed_rent = validate_positive_number(agreed_rent, 'Rent')

    start_dt = date.fromisoformat(str(start_date))
    end_dt = date.fromisoformat(str(end_date))
    if end_dt < start_dt:
        raise ValueError("End date must be on or after start date.")

    conn = check_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
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
            (apartment_id, tenant_id, start_date, end_date, agreed_rent),
        )
        lease_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE Apartments
            SET occupancy_status = 'Occupied'
            WHERE apartment_id = ?
            """,
            (apartment_id,),
        )

        # Generate initial monthly payment rows only up to one month in advance.
        payments_created = sync_lease_payments_up_to_horizon(conn=conn, lease_id=lease_id, months_ahead=1)

        conn.commit()
        return {"lease_id": lease_id, "payments_created": payments_created}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================================
# UPDATE / TERMINATION
# ============================================================================

def update_lease(lease_id, start_date, end_date, agreed_rent):
    validate_required_fields({
        'lease_id': lease_id,
        'start_date': start_date,
        'end_date': end_date,
        'agreed_rent': agreed_rent
    })

    agreed_rent = validate_positive_number(agreed_rent, 'Rent')

    execute_query(
        """
        UPDATE Lease
        SET start_date = ?, end_date = ?, Agreed_rent = ?
        WHERE lease_id = ?
        """,
        (start_date, end_date, agreed_rent, lease_id),
        'none'
    )


def update_lease_early_termination(lease_id, fee):
    execute_query(
        "UPDATE Lease SET early_termination_fee = ? WHERE lease_id = ?",
        (fee, lease_id),
        'none'
    )