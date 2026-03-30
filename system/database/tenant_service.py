from .db_utils import execute_query, execute_transaction


def get_all_tenants(city_id=None):
    query = """
        SELECT
            t.tenant_id,
            u.first_name,
            u.surname,
            ua.email,
            t.telephone,
            tr.reference,
            tr.reference_email,
            t.ni_number,
            CASE
                WHEN l.start_date IS NOT NULL AND l.end_date IS NOT NULL
                THEN CAST(ROUND((julianday(l.end_date) - julianday(l.start_date)) / 30.0) AS INTEGER) || ' months'
                ELSE '-'
            END AS lease_period,
            COALESCE(a.type, '-') AS apartment_type,
            t.occupation
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
        JOIN User_Access ua ON u.user_id = ua.user_id
        LEFT JOIN Tenant_Reference tr ON t.tenant_id = tr.tenant_id
        LEFT JOIN Lease l ON l.lease_id = (
            SELECT l2.lease_id
            FROM Lease l2
            WHERE l2.tenant_id = t.tenant_id
            ORDER BY
                CASE WHEN DATE(l2.end_date) >= DATE('now') THEN 0 ELSE 1 END,
                DATE(l2.start_date) DESC,
                l2.lease_id DESC
            LIMIT 1
        )
        LEFT JOIN Apartments a ON a.apartment_id = l.apartment_id
    """

    params = []
    if city_id is not None:
        query += " WHERE u.city_id = ?"
        params.append(city_id)

    query += " ORDER BY t.tenant_id ASC"
    return execute_query(query, tuple(params))


def create_tenant(first_name, surname, email, telephone, reference_name, reference_email,
                  ni_number, lease_period, apartment_type, occupation, city_id=None, password_plain=None):
    from database.databaseConnection import check_connection
    from database.user_service import _hash_password_with_name_key
    
    conn = check_connection()
    cursor = conn.cursor()

    city_id = int(city_id) if city_id is not None else 1

    try:
        cursor.execute(
            "INSERT INTO User (city_id, first_name, surname) VALUES (?, ?, ?)",
            (city_id, first_name, surname)
        )
        new_user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES (?, ?, ?, ?)",
            (
                new_user_id,
                _hash_password_with_name_key(password_plain, first_name, surname),
                6,
                email,
            )
        )

        cursor.execute("""
            INSERT INTO Tenant (user_id, ni_number, telephone, occupation)
            VALUES (?, ?, ?, ?)
        """, (new_user_id, ni_number, telephone, occupation))

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
        ("UPDATE Tenant SET ni_number = ?, telephone = ?, occupation = ? WHERE tenant_id = ?",
         (ni_number, telephone, occupation, tenant_id)),
        ("UPDATE Tenant_Reference SET reference = ?, reference_email = ? WHERE tenant_id = ?",
         (reference_name, reference_email, tenant_id))
    ]
    execute_transaction(operations)


def delete_tenant(tenant_id):
    user_id_row = execute_query("SELECT user_id FROM Tenant WHERE tenant_id = ?", (tenant_id,), 'one')
    if not user_id_row:
        raise ValueError("Tenant not found.")

    user_id = user_id_row[0]

    # Keep a snapshot of apartments linked to this tenant before lease deletion.
    tenant_apartments = execute_query(
        "SELECT DISTINCT apartment_id FROM Lease WHERE tenant_id = ?",
        (tenant_id,),
    ) or []
    apartment_ids = [row[0] for row in tenant_apartments if row and row[0] is not None]

    # Build optional cleanup operations for tables that may not exist in older DB files.
    table_exists = {
        "Early_Termination_Request": execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Early_Termination_Request'",
            (),
            'one',
        ) is not None,
    }

    operations = [
        # Remove dependent records first to avoid FK issues.
        (
            "DELETE FROM Maintenance_Assignment WHERE request_id IN ("
            "SELECT request_id FROM Maintenance_Request WHERE tenant_id = ?)",
            (tenant_id,),
        ),
        (
            "DELETE FROM Payment WHERE lease_id IN ("
            "SELECT lease_id FROM Lease WHERE tenant_id = ?)",
            (tenant_id,),
        ),
        ("DELETE FROM Complaints WHERE tenant_id = ?", (tenant_id,)),
        ("DELETE FROM Maintenance_Request WHERE tenant_id = ?", (tenant_id,)),
    ]

    if table_exists["Early_Termination_Request"]:
        operations.append(("DELETE FROM Early_Termination_Request WHERE tenant_id = ?", (tenant_id,)))

    operations.extend([
        ("DELETE FROM Tenant_Reference WHERE tenant_id = ?", (tenant_id,)),
        ("DELETE FROM Lease WHERE tenant_id = ?", (tenant_id,)),
        ("DELETE FROM Tenant WHERE tenant_id = ?", (tenant_id,)),
        ("DELETE FROM User_Access WHERE user_id = ?", (user_id,)),
        ("DELETE FROM User WHERE user_id = ?", (user_id,)),
    ])

    # After removing tenant leases, free up apartments that now have no active lease.
    for apartment_id in apartment_ids:
        operations.append(
            (
                "UPDATE Apartments "
                "SET occupancy_status = 'Vacant' "
                "WHERE apartment_id = ? "
                "AND NOT EXISTS ("
                "    SELECT 1 FROM Lease l "
                "    WHERE l.apartment_id = ? "
                "      AND DATE(COALESCE(l.end_date, DATE('now'))) >= DATE('now') "
                "      AND COALESCE(l.early_termination_fee, 0) = 0"
                ")",
                (apartment_id, apartment_id),
            )
        )

    ok = execute_transaction(operations)
    if not ok:
        raise RuntimeError("Failed to delete tenant and related records.")


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


def get_all_complaints_with_tenant(city_id=None):
    query = """
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
    """

    params = []
    if city_id is not None:
        query += " WHERE u.city_id = ?"
        params.append(city_id)

    query += " ORDER BY c.complaint_id ASC"
    return execute_query(query, tuple(params))