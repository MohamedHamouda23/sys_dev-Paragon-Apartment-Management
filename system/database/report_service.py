from database.databaseConnection import check_connection

def query_db(sql, params=()):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_summary_snapshot(city_id=None):
    where = ""
    params = ()
    if city_id is not None:
        where = " WHERE a.city_id = ?"
        params = (city_id,)

    apartment_stats = query_db(
        f"""
        SELECT
            COUNT(*) AS total_apartments,
            SUM(CASE WHEN a.occupancy_status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_apartments
        FROM Apartments a
        {where}
        """,
        params,
    )
    total_apartments, occupied_apartments = apartment_stats[0]
    total_apartments = total_apartments or 0
    occupied_apartments = occupied_apartments or 0

    financial_where = ""
    financial_params = ()
    if city_id is not None:
        financial_where = " WHERE a.city_id = ?"
        financial_params = (city_id,)

    finance_stats = query_db(
        f"""
        SELECT
            COALESCE(SUM(CASE WHEN p.payment_date IS NOT NULL THEN p.amount ELSE 0 END), 0) AS collected,
            COALESCE(SUM(CASE WHEN p.payment_date IS NULL THEN p.amount ELSE 0 END), 0) AS pending
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        {financial_where}
        """,
        financial_params,
    )
    collected, pending = finance_stats[0]

    maintenance_where = ""
    maintenance_params = ()
    if city_id is not None:
        maintenance_where = " WHERE a.city_id = ?"
        maintenance_params = (city_id,)

    maintenance_cost = query_db(
        f"""
        SELECT COALESCE(SUM(mr.repair_cost), 0)
        FROM Maintenance_Request mr
        JOIN Apartments a ON mr.apartment_id = a.apartment_id
        {maintenance_where}
        """,
        maintenance_params,
    )[0][0]

    occupancy_rate = round((occupied_apartments / total_apartments) * 100, 2) if total_apartments else 0.0

    return {
        "apartments": total_apartments,
        "occupancy_rate": occupancy_rate,
        "collected": float(collected or 0),
        "pending": float(pending or 0),
        "maintenance": float(maintenance_cost or 0),
    }

def fetch_occupancy_rows(city_id=None):
    sql = """
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
    params = ()
    if city_id is not None:
        sql += " WHERE a.city_id = ?"
        params = (city_id,)
    sql += " ORDER BY l.city_name, a.apartment_id"
    return query_db(sql, params)

def fetch_financial_rows(city_id=None, late_filter="All", paid_filter="All"):
    late_filter = (late_filter or "All").strip().lower()
    paid_filter = (paid_filter or "All").strip().lower()

    sql = """
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
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += " ORDER BY p.due_date DESC, p.payment_id DESC"
    return query_db(sql, tuple(params))

def fetch_maintenance_rows(city_id=None):
    sql = """
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
    params = ()
    if city_id is not None:
        sql += " WHERE a.city_id = ?"
        params = (city_id,)
    sql += " ORDER BY mr.request_id DESC"
    return query_db(sql, params)