from database.databaseConnection import check_connection,fetch_all, insert


def get_all_requests():
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            mr.request_id,
            u.first_name || ' ' || u.surname AS tenant_name,
            mr.issue,
            DATE(mr.created_date) AS created_date,  
            mr.Maintenance_status
        FROM Maintenance_Request mr
        JOIN Tenant t ON mr.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON mr.apartment_id = a.apartment_id
        ORDER BY mr.created_date DESC
    """)
    results = cursor.fetchall()
    conn.close()
    return results


def viewFull(request_id):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            mr.request_id,
            mr.issue,
            mr.description,
            mr.priority,
            mr.created_date,
            mr.resolved_date,
            mr.Maintenance_status,
            mr.notes,
            u.first_name || ' ' || u.surname AS tenant_name,
            a.type,
            b.postcode,
            su.first_name || ' ' || su.surname AS staff_name,
            ma.assigned_date,
            ma.is_current
        FROM Maintenance_Request mr
        LEFT JOIN Tenant t
            ON mr.tenant_id = t.tenant_id
        LEFT JOIN User u
            ON t.user_id = u.user_id
        LEFT JOIN Apartments a
            ON mr.apartment_id = a.apartment_id
        LEFT JOIN Buildings b
            ON a.building_id = b.building_id
        LEFT JOIN Maintenance_Assignment ma
            ON mr.request_id = ma.request_id
            AND ma.is_current = 1
        LEFT JOIN Employee e
            ON ma.employee_id = e.employee_id
        LEFT JOIN User su
            ON e.employee_id = su.user_id
        WHERE mr.request_id = ?
        ORDER BY mr.created_date DESC
    """, (request_id,))
    result = cursor.fetchone()
    conn.close()
    return result