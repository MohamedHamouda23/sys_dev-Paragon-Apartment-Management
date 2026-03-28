from .db_utils import execute_query, build_city_filter


def fetch_summary_snapshot(city_id=None):
    """Fetch summary statistics for apartments, finance, and maintenance."""
    
    # Apartment statistics
    query, params = build_city_filter(
        """
        SELECT
            COUNT(*) AS total_apartments,
            SUM(CASE WHEN a.occupancy_status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_apartments
        FROM Apartments a
        """,
        "a.city_id",
        user_info=(None, None, None, None, None, city_id) if city_id else None
    )
    apartment_stats = execute_query(query, params, 'one')
    total_apartments = apartment_stats[0] or 0
    occupied_apartments = apartment_stats[1] or 0

    # Financial statistics
    query, params = build_city_filter(
        """
        SELECT
            COALESCE(SUM(CASE WHEN p.payment_date IS NOT NULL THEN p.amount ELSE 0 END), 0) AS collected,
            COALESCE(SUM(CASE WHEN p.payment_date IS NULL THEN p.amount ELSE 0 END), 0) AS pending
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        """,
        "a.city_id",
        user_info=(None, None, None, None, None, city_id) if city_id else None
    )
    finance_stats = execute_query(query, params, 'one')
    collected, pending = finance_stats

    # Maintenance cost
    query, params = build_city_filter(
        """
        SELECT COALESCE(SUM(mr.repair_cost), 0)
        FROM Maintenance_Request mr
        JOIN Apartments a ON mr.apartment_id = a.apartment_id
        """,
        "a.city_id",
        user_info=(None, None, None, None, None, city_id) if city_id else None
    )
    maintenance_cost = execute_query(query, params, 'one')[0]

    occupancy_rate = round((occupied_apartments / total_apartments) * 100, 2) if total_apartments else 0.0

    return {
        "apartments": total_apartments,
        "occupancy_rate": occupancy_rate,
        "collected": float(collected or 0),
        "pending": float(pending or 0),
        "maintenance": float(maintenance_cost or 0),
    }


def fetch_occupancy_rows(city_id=None):
    """Fetch occupancy data for all apartments."""
    query = """
        SELECT
            a.apartment_id,
            l.city_name,
            b.street || ' (' || b.postcode || ')' AS building,
            a.type,
            a.num_rooms,
            a.occupancy_status
        FROM Apartments a
        JOIN Location l ON a.city_id = l.city_id
        JOIN Buildings b ON a.building_id = b.building_id
    """
    
    if city_id is not None:
        query += " WHERE a.city_id = ?"
        params = (city_id,)
    else:
        params = ()
    
    query += " ORDER BY l.city_name, a.apartment_id"
    return execute_query(query, params)


def fetch_financial_rows(city_id=None, late_filter="All", paid_filter="All"):
    """Fetch financial payment data with optional filters."""
    late_filter = (late_filter or "All").strip().lower()
    paid_filter = (paid_filter or "All").strip().lower()

    query = """
        SELECT
            p.payment_id,
            l2.city_name,
            u.first_name || ' ' || u.surname AS tenant_name,
            DATE(p.due_date) AS due_date,
            ROUND(p.amount, 2) AS amount,
            CASE
                WHEN p.payment_date IS NOT NULL THEN 'Yes'
                ELSE 'No'
            END AS is_paid,
            CASE
                WHEN COALESCE(p.Is_late, 0) = 1 THEN 'Yes'
                ELSE 'No'
            END AS is_late
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Location l2 ON a.city_id = l2.city_id
    """
    
    where_clauses = []
    params = []
    
    if city_id is not None:
        where_clauses.append("a.city_id = ?")
        params.append(city_id)

    if paid_filter == "paid":
        where_clauses.append("p.payment_date IS NOT NULL")
    elif paid_filter == "not paid":
        where_clauses.append("p.payment_date IS NULL")

    if late_filter == "late":
        where_clauses.append("COALESCE(p.Is_late, 0) = 1")
    elif late_filter == "not late":
        where_clauses.append("COALESCE(p.Is_late, 0) = 0")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY p.due_date DESC, p.payment_id DESC"
    return execute_query(query, tuple(params))


def fetch_maintenance_rows(city_id=None):
    """Fetch maintenance request data."""
    query = """
        SELECT
            mr.request_id,
            l.city_name,
            b.postcode AS building,
            mr.issue,
            mr.Maintenance_status,
            COALESCE(ROUND(mr.repair_cost, 2), 0) AS repair_cost,
            COALESCE(DATE(mr.resolved_date), '-') AS resolved_date
        FROM Maintenance_Request mr
        JOIN Apartments a ON mr.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        JOIN Location l ON a.city_id = l.city_id
    """
    
    if city_id is not None:
        query += " WHERE a.city_id = ?"
        params = (city_id,)
    else:
        params = ()
    
    query += " ORDER BY mr.request_id DESC"
    return execute_query(query, params)