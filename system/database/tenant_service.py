from .db_utils import execute_query, execute_transaction


def get_all_tenants():
    return execute_query("""
        SELECT
            t.tenant_id,
            u.first_name,
            u.surname,
            ua.email,
            t.telephone,
            tr.reference,
            tr.reference_email,
            t.ni_number,
            t.lease_period,
            t.apartment_type,
            t.occupation
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
        JOIN User_Access ua ON u.user_id = ua.user_id
        LEFT JOIN Tenant_Reference tr ON t.tenant_id = tr.tenant_id
        ORDER BY t.tenant_id ASC
    """)


def create_tenant(first_name, surname, email, telephone, reference_name, reference_email,
                  ni_number, lease_period, apartment_type, occupation):
    from database.databaseConnection import check_connection
    
    conn = check_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO User (city_id, first_name, surname) VALUES (?, ?, ?)",
            (1, first_name, surname)
        )
        new_user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES (?, ?, ?, ?)",
            (new_user_id, "tenant_default", 6, email)
        )

        cursor.execute("""
            INSERT INTO Tenant (user_id, ni_number, telephone, occupation, apartment_type, lease_period)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_user_id, ni_number, telephone, occupation, apartment_type, lease_period))

        new_tenant_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO Tenant_Reference (tenant_id, reference, reference_email)
            VALUES (?, ?, ?)
        """, (new_tenant_id, reference_name, reference_email))

        conn.commit()
    finally:
        conn.close()


def update_tenant(tenant_id, first_name, surname, email, telephone, reference_name, reference_email,
                  ni_number, lease_period, apartment_type, occupation):
    from database.databaseConnection import check_connection
    
    user_id_row = execute_query("SELECT user_id FROM Tenant WHERE tenant_id = ?", (tenant_id,), 'one')
    user_id = user_id_row[0]

    operations = [
        ("UPDATE User SET first_name = ?, surname = ? WHERE user_id = ?", 
         (first_name, surname, user_id)),
        ("UPDATE User_Access SET email = ? WHERE user_id = ?", 
         (email, user_id)),
        ("UPDATE Tenant SET ni_number = ?, telephone = ?, occupation = ?, apartment_type = ?, lease_period = ? WHERE tenant_id = ?",
         (ni_number, telephone, occupation, apartment_type, lease_period, tenant_id)),
        ("UPDATE Tenant_Reference SET reference = ?, reference_email = ? WHERE tenant_id = ?",
         (reference_name, reference_email, tenant_id))
    ]
    execute_transaction(operations)


def delete_tenant(tenant_id):
    user_id_row = execute_query("SELECT user_id FROM Tenant WHERE tenant_id = ?", (tenant_id,), 'one')
    user_id = user_id_row[0]

    operations = [
        ("DELETE FROM Tenant_Reference WHERE tenant_id = ?", (tenant_id,)),
        ("DELETE FROM Tenant WHERE tenant_id = ?", (tenant_id,)),
        ("DELETE FROM User_Access WHERE user_id = ?", (user_id,)),
        ("DELETE FROM User WHERE user_id = ?", (user_id,))
    ]
    execute_transaction(operations)


# ============================================================================
# COMPLAINTS
# ============================================================================

def get_complaints_for_tenant(tenant_id):
    return execute_query("""
        SELECT complaint_id, description, date_submitted
        FROM Complaints
        WHERE tenant_id = ?
        ORDER BY complaint_id ASC
    """, (tenant_id,))


def add_complaint(tenant_id, description):
    execute_query("""
        INSERT INTO Complaints (tenant_id, description, date_submitted)
        VALUES (?, ?, DATE('now'))
    """, (tenant_id, description), 'none')


def delete_complaint(complaint_id):
    execute_query("DELETE FROM Complaints WHERE complaint_id = ?", (complaint_id,), 'none')


def get_all_complaints_with_tenant():
    return execute_query("""
        SELECT 
            c.complaint_id,
            t.tenant_id,
            u.first_name,
            u.surname,
            c.description,
            c.date_submitted
        FROM Complaints c
        JOIN Tenant t ON c.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        ORDER BY c.complaint_id ASC
    """)