from database.databaseConnection import check_connection
from datetime import datetime


def get_all_requests(user_info=None):
    """Get all maintenance requests, filtered by user's city if provided."""
    conn = check_connection()
    cursor = conn.cursor()
    
    query = """
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
        JOIN Buildings b ON a.building_id = b.building_id
    """
    
    # Add city filter if user_info contains city
    params = ()
    if user_info and isinstance(user_info, dict) and user_info.get('city'):
        query += " WHERE b.city_id = (SELECT city_id FROM Location WHERE city_name = ?)"
        params = (user_info['city'],)
    
    query += " ORDER BY mr.created_date DESC"
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    return results


def viewFull(request_id):
    """Get full details of a specific maintenance request."""
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            mr.request_id,
            mr.description,
            mr.priority,
            mr.created_date,
            mr.resolved_date,
            mr.Maintenance_status,
            mr.notes,
            mr.issue,
            u.first_name || ' ' || u.surname AS tenant_name,
            a.type,
            b.postcode,
            su.first_name || ' ' || su.surname AS staff_name,
            ma.assigned_date,
            ma.is_current
        FROM Maintenance_Request mr
        LEFT JOIN Tenant t ON mr.tenant_id = t.tenant_id
        LEFT JOIN User u ON t.user_id = u.user_id
        LEFT JOIN Apartments a ON mr.apartment_id = a.apartment_id
        LEFT JOIN Buildings b ON a.building_id = b.building_id
        LEFT JOIN Maintenance_Assignment ma ON mr.request_id = ma.request_id AND ma.is_current = 1
        LEFT JOIN Employee e ON ma.employee_id = e.employee_id
        LEFT JOIN User su ON e.employee_id = su.user_id
        WHERE mr.request_id = ?
    """, (request_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def update_request_status(request_id, action):
    """Update request status: approve, reject, or resolve."""
    action_map = {
        "approve": "In Progress",  
        "reject":  "Denied",
        "resolve": "Resolved",
    }
    if action.lower() not in action_map:
        raise ValueError("Action must be 'approve', 'reject', or 'resolve'")

    new_status = action_map[action.lower()]
    
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        if new_status == "Resolved":
            cursor.execute("""
                UPDATE Maintenance_Request
                SET Maintenance_status = ?,
                    resolved_date = ?
                WHERE request_id = ?
            """, (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), request_id))
        else:
            cursor.execute("""
                UPDATE Maintenance_Request
                SET Maintenance_status = ?
                WHERE request_id = ?
            """, (new_status, request_id))
        
        conn.commit()
        
        cursor.execute("""
            SELECT request_id, Maintenance_status
            FROM Maintenance_Request
            WHERE request_id = ?
        """, (request_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Database error:", e)
        return None


def get_maintenance_staff(user_info=None):
    """Get only Maintenance Staff employees, filtered by city if provided."""
    conn = check_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT e.employee_id,
               u.first_name || ' ' || u.surname AS full_name
        FROM Employee e
        JOIN User u ON e.employee_id = u.user_id
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        WHERE r.role_name = 'Maintenance Staff'
    """
    
    # Add city filter if user_info contains city
    params = ()
    if user_info and isinstance(user_info, dict) and user_info.get('city'):
        query += " AND u.city_id = (SELECT city_id FROM Location WHERE city_name = ?)"
        params = (user_info['city'],)
    
    query += " ORDER BY full_name"
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    return results


def get_staff_task_count_for_date(staff_name, date_str):
    """
    Get task count for each time slot (09:00, 13:00, 17:00) for a staff member on a specific date.
    Returns dict: {'09:00': count, '13:00': count, '17:00': count}
    Each slot can have maximum 1 task.
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ma.assigned_date
        FROM Maintenance_Assignment ma
        JOIN Employee e ON ma.employee_id = e.employee_id
        JOIN User u ON e.employee_id = u.user_id
        WHERE (u.first_name || ' ' || u.surname) = ?
        AND DATE(ma.assigned_date) = ?
        AND ma.is_current = 1
    """, (staff_name, date_str))
    
    assignments = cursor.fetchall()
    conn.close()
    
    # Count tasks per slot
    slot_counts = {}
    for assignment in assignments:
        if assignment[0]:
            # Extract time portion (HH:MM)
            time_part = assignment[0][11:16]if ' ' in assignment[0] else assignment[0][:5]
            slot_counts[time_part] = slot_counts.get(time_part, 0) + 1
    
    return slot_counts


def assign_and_schedule(request_id, employee_id, priority, date_str, comment):
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        assigned_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # You need to get the selected time slot from somewhere
        # This assumes you'll pass it as an additional parameter
        # For now, let's use a default or you need to modify the function signature
        
        # For demonstration, I'll assume you'll pass scheduled_datetime
        # But you'll need to modify the calling code to include the time slot
        
        # Retire any existing current assignment
        cursor.execute("""
            UPDATE Maintenance_Assignment
            SET is_current = 0
            WHERE request_id = ? AND is_current = 1
        """, (request_id,))

        # Insert new assignment
        cursor.execute("""
            INSERT INTO Maintenance_Assignment 
            (request_id, employee_id, assigned_date, is_current)
            VALUES (?, ?, ?, 1)
        """, (request_id, employee_id, assigned_date))

        # Update request with priority and status
        cursor.execute("""
            UPDATE Maintenance_Request
            SET Maintenance_status = 'In Progress',
                priority = ?
            WHERE request_id = ?
        """, (priority, request_id))

        conn.commit()

        # Return the assignment details
        cursor.execute("""
            SELECT ma.request_id, ma.employee_id, ma.assigned_date,
                   u.first_name || ' ' || u.surname AS staff_name
            FROM Maintenance_Assignment ma
            JOIN Employee e ON ma.employee_id = e.employee_id
            JOIN User u ON e.employee_id = u.user_id
            WHERE ma.request_id = ? AND ma.is_current = 1
        """, (request_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

def resolve_request(request_id, issue, description, repair_time=None, repair_cost=None):
    """Mark a request as Resolved, saving updated issue and resolution notes."""
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Maintenance_Request
            SET Maintenance_status = 'Resolved',
                resolved_date      = ?,
                issue              = ?,
                notes              = ?,
                repair_time        = ?,
                repair_cost        = ?
            WHERE request_id = ?
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            issue,
            description,
            repair_time,
            repair_cost,
            request_id,
        ))
        conn.commit()
        
        cursor.execute(
            "SELECT request_id FROM Maintenance_Request WHERE request_id = ?",
            (request_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Database error:", e)
        return None


def get_all_tenants(user_info=None):
    """
    Return [(tenant_id, 'First Surname'), …] for all tenants.
    Filtered by city if user_info is provided.
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT t.tenant_id,
               u.first_name || ' ' || u.surname AS full_name
        FROM Tenant t
        JOIN User u ON u.user_id = t.user_id
    """
    
    # Add city filter if user_info contains city
    params = ()
    if user_info and isinstance(user_info, dict) and user_info.get('city'):
        query += " WHERE u.city_id = (SELECT city_id FROM Location WHERE city_name = ?)"
        params = (user_info['city'],)
    
    query += " ORDER BY full_name"
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def get_all_apartments(user_info=None):
    """
    Return [(apartment_id, 'Apt #N — Type (Postcode)'), …].
    Filtered by city if user_info is provided.
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT a.apartment_id,
               'Apt #' || a.apartment_id || ' — ' || a.type || ' (' || b.postcode || ')' AS label
        FROM Apartments a
        JOIN Buildings b ON b.building_id = a.building_id
    """
    
    # Add city filter if user_info contains city
    params = ()
    if user_info and isinstance(user_info, dict) and user_info.get('city'):
        query += " WHERE b.city_id = (SELECT city_id FROM Location WHERE city_name = ?)"
        params = (user_info['city'],)
    
    query += " ORDER BY a.apartment_id"
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def register_request(apartment_id, tenant_id, issue, description, priority):
    """
    FR4.5 — Insert a new Maintenance_Request row with status 'Open'.
    Returns the new request_id on success, or None on failure.
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Maintenance_Request
                (apartment_id, tenant_id, issue, description,
                 Maintenance_status, priority, created_date)
            VALUES (?, ?, ?, ?, 'Open', ?, ?)
        """, (
            apartment_id, tenant_id, issue, description,
            priority, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Database error:", e)
        return None