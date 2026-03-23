# ============================================================================
# MAINTENANCE SERVICE MODULE
# Database operations for maintenance management
# ============================================================================

from database.databaseConnection import check_connection
from datetime import datetime


def get_all_requests(user_info=None, selected_city=None):
    """
    Get all maintenance requests.
    - For managers: retrieves data from ALL cities OR filtered by city name
    - For other roles (including Administrators): retrieves data filtered by user's assigned city only
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    if is_manager:
        # Manager query: Include city_name column
        query = """
            SELECT 
                mr.request_id,
                u.first_name || ' ' || u.surname AS tenant_name,
                mr.issue,
                DATE(mr.created_date) AS created_date,
                mr.Maintenance_status,
                l.city_name
            FROM Maintenance_Request mr
            JOIN Tenant t ON mr.tenant_id = t.tenant_id
            JOIN User u ON t.user_id = u.user_id
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            JOIN Buildings b ON a.building_id = b.building_id
            JOIN Location l ON b.city_id = l.city_id
        """
        params = ()
        # Apply city filter if a specific city is selected
        if selected_city and selected_city != "All Cities":
            query += " WHERE l.city_name = ?"
            params = (selected_city,)
            
        query += " ORDER BY mr.created_date DESC"
        cursor.execute(query, params)
    else:
        # Non-manager query: Filter by user's assigned city_id
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
        params = ()
        # retrive_data returns city_id at index 5
        if user_info and len(user_info) > 5 and user_info[5]:
            query += " WHERE b.city_id = ?"
            params = (user_info[5],)
        
        query += " ORDER BY mr.created_date DESC"
        cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    return results


def viewFull(request_id):
    """Get full details of a specific maintenance request"""
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
            a.type AS apartment_type,
            b.postcode,
            su.first_name || ' ' || su.surname AS staff_name,
            ma.assigned_date,
            ma.is_current,
            mr.repair_cost,
            mr.repair_time
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
    """Update request status: approve, reject, or resolve"""
    action_map = {
        "approve": "Approved",
        "reject": "Denied",
        "resolve": "Resolved",
    }
    if action.lower() not in action_map:
        raise ValueError("Action must be 'approve', 'reject', or 'resolve'")

    new_status = action_map[action.lower()]
    
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        if new_status == "Resolved":
            # Set resolved date when marking as resolved
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
        return True
    except Exception as e:
        conn.rollback()
        print("Database error:", e)
        return False
    finally:
        conn.close()


def get_maintenance_staff(user_info=None):
    """
    Get only Maintenance Staff employees.
    - For managers: retrieves staff from ALL cities
    - For other roles: filtered by user's assigned city
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    query = """
        SELECT e.employee_id,
               u.first_name || ' ' || u.surname AS full_name
        FROM Employee e
        JOIN User u ON e.employee_id = u.user_id
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        WHERE r.role_name = 'Maintenance Staff'
    """
    
    params = ()
    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        query += " AND u.city_id = ?"
        params = (user_info[5],)
    
    query += " ORDER BY full_name"
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    return results


def get_staff_task_count_for_date(staff_name, date_str):
    """
    Get task count for each time slot (09:00, 13:00, 17:00) for a staff member on a specific date.
    Returns dict: {'09:00': count, '13:00': count, '17:00': count}
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Get employee_id from staff name
    cursor.execute("""
        SELECT e.employee_id
        FROM Employee e
        JOIN User u ON e.employee_id = u.user_id
        WHERE (u.first_name || ' ' || u.surname) = ?
    """, (staff_name,))
    
    employee_result = cursor.fetchone()
    if not employee_result:
        conn.close()
        return {}
    
    employee_id = employee_result[0]
    
    # Get all assignments for the date
    cursor.execute("""
        SELECT strftime('%H:%M', assigned_date) as time_slot
        FROM Maintenance_Assignment
        WHERE employee_id = ?
        AND DATE(assigned_date) = ?
        AND is_current = 1
    """, (employee_id, date_str))
    
    assignments = cursor.fetchall()
    conn.close()
    
    # Count tasks per time slot
    slot_counts = {}
    for assignment in assignments:
        if assignment[0]:
            time_slot = assignment[0]
            slot_counts[time_slot] = slot_counts.get(time_slot, 0) + 1
    
    return slot_counts


def assign_and_schedule(request_id, employee_id, priority, scheduled_datetime, comment):
    """Assign staff and schedule maintenance with correct date and time"""
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        # Check if staff is already assigned at this time
        cursor.execute("""
            SELECT COUNT(*)
            FROM Maintenance_Assignment
            WHERE employee_id = ?
              AND assigned_date = ?
              AND is_current = 1
        """, (employee_id, scheduled_datetime))
        
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            raise Exception("Staff member is already assigned to another task at this time")
        
        # Mark previous assignments as not current
        cursor.execute("""
            UPDATE Maintenance_Assignment
            SET is_current = 0
            WHERE request_id = ?
        """, (request_id,))
        
        # Insert new assignment
        cursor.execute("""
            INSERT INTO Maintenance_Assignment 
            (request_id, employee_id, assigned_date, is_current)
            VALUES (?, ?, ?, 1)
        """, (request_id, employee_id, scheduled_datetime))
        
        # Update request status and description
        cursor.execute("""
            UPDATE Maintenance_Request
            SET Maintenance_status = 'In Progress',
                priority = ?,
                description = ?
            WHERE request_id = ?
        """, (priority, comment, request_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_request_priority(request_id, new_priority):
    """Update priority of a maintenance request"""
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Maintenance_Request
            SET priority = ?
            WHERE request_id = ?
        """, (new_priority, request_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Database error:", e)
        return False
    finally:
        conn.close()


def resolve_request(request_id, notes, repair_cost, repair_time):
    """Mark a maintenance request as resolved"""
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Maintenance_Request
            SET Maintenance_status = 'Resolved',
                resolved_date = ?,
                notes = ?,
                repair_cost = ?,
                repair_time = ?
            WHERE request_id = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes, repair_cost, repair_time, request_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Database error:", e)
        return False
    finally:
        conn.close()


def register_request(apartment_id, tenant_id, issue, priority):
    """Register a new maintenance request"""
    conn = check_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Maintenance_Request 
            (apartment_id, tenant_id, issue, priority, Maintenance_status, created_date)
            VALUES (?, ?, ?, ?, 'Open', ?)
        """, (apartment_id, tenant_id, issue, priority, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        new_id = cursor.lastrowid
        conn.commit()
        return new_id
    except Exception as e:
        conn.rollback()
        print("Database error:", e)
        return None
    finally:
        conn.close()


def get_all_tenants(user_info=None):
    """
    Get all tenants.
    - For managers: all tenants from ALL cities
    - For other roles: tenants filtered by user's assigned city
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    query = """
        SELECT t.tenant_id,
               u.first_name || ' ' || u.surname AS full_name
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
    """
    
    params = ()
    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        query += " WHERE u.city_id = ?"
        params = (user_info[5],)
    
    query += " ORDER BY full_name"
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    return results


def get_all_apartments(user_info=None):
    """
    Get all apartments.
    - For managers: all apartments from ALL cities
    - For other roles: apartments filtered by user's assigned city
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    query = """
        SELECT a.apartment_id,
               b.postcode || ' - ' || a.type AS apartment_label
        FROM Apartments a
        JOIN Buildings b ON a.building_id = b.building_id
    """
    
    params = ()
    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        query += " WHERE b.city_id = ?"
        params = (user_info[5],)
    
    query += " ORDER BY b.postcode"
    cursor.execute(query, params)
    
    results = cursor.fetchall()
    conn.close()
    return results


# ============================================================================
# move to file called report_service METRICS FUNCTIONS
# ============================================================================

def get_metrics_summary(user_info=None):
    """
    Get summary metrics for maintenance requests.
    - For managers: metrics from ALL cities
    - For other roles: metrics filtered by user's assigned city
    Returns: (total_requests, completed, pending, in_progress, avg_resolution_time)
    """
    conn = check_connection()
    cursor = conn.cursor()

    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")

    city_join = ""
    where_base = ""
    params = ()

    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        city_join = """
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            JOIN Buildings b ON a.building_id = b.building_id
        """
        where_base = "WHERE b.city_id = ?"
        params = (user_info[5],)

    # Total requests
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM Maintenance_Request mr
        {city_join}
        {where_base}
    """, params)
    total_requests = cursor.fetchone()[0]

    # Completed requests
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM Maintenance_Request mr
        {city_join}
        {where_base} {'AND' if where_base else 'WHERE'}
        mr.Maintenance_status = 'Resolved'
    """, params)
    completed = cursor.fetchone()[0]

    # Pending requests
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM Maintenance_Request mr
        {city_join}
        {where_base} {'AND' if where_base else 'WHERE'}
        mr.Maintenance_status IN ('Open', 'Approved', 'Denied')
    """, params)
    pending = cursor.fetchone()[0]

    # In progress requests
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM Maintenance_Request mr
        {city_join}
        {where_base} {'AND' if where_base else 'WHERE'}
        mr.Maintenance_status = 'In Progress'
    """, params)
    in_progress = cursor.fetchone()[0]

    # Average resolution time in days
    cursor.execute(f"""
        SELECT AVG(
            MAX(0, JULIANDAY(mr.resolved_date) - JULIANDAY(mr.created_date))
        ) as avg_days
        FROM Maintenance_Request mr
        {city_join}
        {where_base} {'AND' if where_base else 'WHERE'}
        mr.resolved_date IS NOT NULL
        AND mr.created_date IS NOT NULL
        AND mr.resolved_date >= mr.created_date
    """, params)

    result = cursor.fetchone()
    avg_resolution_time = round(result[0], 2) if result and result[0] else 0.0

    conn.close()
    return (total_requests, completed, pending, in_progress, avg_resolution_time)


def get_cost_analysis(user_info=None):
    """
    Get cost analysis metrics.
    - For managers: cost data from ALL cities
    - For other roles: cost data filtered by user's assigned city
    Returns: (total_cost, avg_cost, max_cost, min_cost)
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    query = """
        SELECT 
            COALESCE(SUM(repair_cost), 0) as total_cost,
            COALESCE(AVG(repair_cost), 0) as avg_cost,
            COALESCE(MAX(repair_cost), 0) as max_cost,
            COALESCE(MIN(repair_cost), 0) as min_cost
        FROM Maintenance_Request mr
    """
    
    params = ()
    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        query += """
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            JOIN Buildings b ON a.building_id = b.building_id
            WHERE b.city_id = ?
            AND mr.repair_cost IS NOT NULL
        """
        params = (user_info[5],)
    else:
        query += " WHERE mr.repair_cost IS NOT NULL"
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return tuple(round(float(x), 2) if x else 0.0 for x in result)
    return (0.0, 0.0, 0.0, 0.0)


def get_staff_performance(user_info=None):
    """
    Get staff performance metrics.
    - For managers: staff performance from ALL cities
    - For other roles: staff performance filtered by user's assigned city
    Returns: [(staff_name, completed_tasks, avg_resolution_days), ...]
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    query = """
        SELECT 
            u.first_name || ' ' || u.surname AS staff_name,
            COUNT(DISTINCT mr.request_id) as completed_tasks,
            ROUND(AVG(JULIANDAY(mr.resolved_date) - JULIANDAY(mr.created_date)), 2) as avg_days
        FROM Maintenance_Assignment ma
        JOIN Employee e ON ma.employee_id = e.employee_id
        JOIN User u ON e.employee_id = u.user_id
        JOIN Maintenance_Request mr ON ma.request_id = mr.request_id
    """
    
    params = ()
    where_clauses = []
    
    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        query += """
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            JOIN Buildings b ON a.building_id = b.building_id
        """
        where_clauses.append("b.city_id = ?")
        params = (user_info[5],)
    
    where_clauses.append("mr.Maintenance_status = 'Resolved'")
    where_clauses.append("mr.resolved_date IS NOT NULL")
    where_clauses.append("mr.created_date IS NOT NULL")
    where_clauses.append("mr.resolved_date >= mr.created_date")
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " GROUP BY staff_name ORDER BY completed_tasks DESC LIMIT 5"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results


def get_recent_completed_requests(user_info=None, limit=5):
    """
    Get recently completed maintenance requests.
    - For managers: recent completions from ALL cities
    - For other roles: recent completions filtered by user's assigned city
    Returns: [(request_id, issue, tenant_name, completed_date, resolution_days), ...]
    """
    conn = check_connection()
    cursor = conn.cursor()
    
    # Check if user is a manager
    is_manager = False
    if user_info and len(user_info) > 4:
        is_manager = (user_info[4] == "Manager")
    
    query = """
        SELECT 
            mr.request_id,
            mr.issue,
            u.first_name || ' ' || u.surname AS tenant_name,
            DATE(mr.resolved_date) as completed_date,
            CAST(JULIANDAY(mr.resolved_date) - JULIANDAY(mr.created_date) AS INTEGER) as resolution_days
        FROM Maintenance_Request mr
        JOIN Tenant t ON mr.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
    """
    
    params = ()
    where_clauses = []
    
    # Non-managers: filter by city (city_id is user_info[5])
    if not is_manager and user_info and len(user_info) > 5 and user_info[5]:
        query += """
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            JOIN Buildings b ON a.building_id = b.building_id
        """
        where_clauses.append("b.city_id = ?")
        params = (user_info[5],)
    
    where_clauses.append("mr.Maintenance_status = 'Resolved'")
    where_clauses.append("mr.resolved_date IS NOT NULL")
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += f" ORDER BY mr.resolved_date DESC LIMIT {limit}"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results