from database.databaseConnection import (
   check_connection
)

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
    print("Fetched maintenance requests:", results)
    conn.close()

    return results