from database.databaseConnection import check_connection, fetch_all, insert
from datetime import datetime


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


def update_request_status(request_id, action):
    # action_map = {
    #     "approve": "Approved",
    #     "reject":  "Denied"
    # }
    # if action.lower() not in action_map:
    #     raise ValueError("Action must be 'approve' or 'reject'")

    # new_status = action_map[action.lower()]
    # conn = check_connection()
    # cursor = conn.cursor()
    # cursor.execute("""
    #     UPDATE Maintenance_Request
    #     SET Maintenance_status = ?
    #     WHERE request_id = ?
    # """, (new_status, request_id))
    # conn.commit()
    # cursor.execute("""
    #     SELECT request_id, Maintenance_status
    #     FROM Maintenance_Request
    #     WHERE request_id = ?
    # """, (request_id,))
    # result = cursor.fetchone()
    # conn.close()
    # return result
    pass



def get_all_staff():
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.employee_id,
               u.first_name || ' ' || u.surname AS full_name
        FROM Employee e
        JOIN User u ON e.employee_id = u.user_id
        ORDER BY full_name
    """)
    results = cursor.fetchall()
    conn.close()
    return results


def assign_staff(request_id, employee_id, notes=None):

    conn = check_connection()
    cursor = conn.cursor()
    try:
        assigned_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE Maintenance_Assignment
            SET is_current = 0
            WHERE request_id = ? AND is_current = 1
        """, (request_id,))

        cursor.execute("""
            INSERT INTO Maintenance_Assignment (request_id, employee_id, assigned_date, is_current)
            VALUES (?, ?, ?, 1)
        """, (request_id, employee_id, assigned_date))

        cursor.execute("""
            UPDATE Maintenance_Request
            SET Maintenance_status = 'In Progress'
            WHERE request_id = ?
        """, (request_id,))

        if notes:
            cursor.execute("""
                UPDATE Maintenance_Request
                SET notes = ?
                WHERE request_id = ?
            """, (notes, request_id))

        conn.commit()

        cursor.execute("""
            SELECT ma.request_id, ma.employee_id, ma.assigned_date, ma.is_current,
                   u.first_name || ' ' || u.surname AS staff_name
            FROM Maintenance_Assignment ma
            JOIN Employee e ON ma.employee_id = e.employee_id
            JOIN User u ON e.employee_id = u.user_id
            WHERE ma.request_id = ? AND ma.is_current = 1
        """, (request_id,))
        result = cursor.fetchone()
        return result

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()