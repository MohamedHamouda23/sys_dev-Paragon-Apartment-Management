# payment_service.py
from database.databaseConnection import check_connection


def update_late_status():
    """Updates the 'is_late' column. Late if past due date and unpaid/underpaid."""
    conn = check_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Payment
        SET is_late = CASE
            WHEN DATE(due_date) < DATE('now')
                 AND (
                     payment_date IS NULL
                     OR amount < (
                         SELECT Agreed_rent
                         FROM Lease
                         WHERE Lease.lease_id = Payment.lease_id
                     )
                 )
            THEN 'Yes'
            ELSE 'No'
        END
        """
    )
    conn.commit()
    conn.close()


def get_tenant_payments(user_id):
    """
    Tenant view:
    - one row per lease
    - only leases from the tenant's own city
    """
    update_late_status()
    conn = check_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            l.lease_id,
            b.street || ' (' || b.postcode || ')' AS apartment,
            COALESCE(MAX(p.due_date), DATE('now')) AS due_date,
            COALESCE(SUM(CASE WHEN p.payment_date IS NOT NULL THEN p.amount ELSE 0 END), 0) AS paid_amount,
            l.Agreed_rent,
            CASE
                WHEN COALESCE(SUM(CASE WHEN p.payment_date IS NOT NULL THEN p.amount ELSE 0 END), 0) >= l.Agreed_rent
                THEN 'Paid'
                ELSE 'Unpaid'
            END AS status,
            MAX(COALESCE(p.is_late, 'No')) AS is_late,
            COALESCE(MAX(p.payment_id), 0) AS payment_id
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        LEFT JOIN Payment p ON p.lease_id = l.lease_id
        WHERE t.user_id = ?
          AND b.city_id = u.city_id
        GROUP BY l.lease_id, apartment, l.Agreed_rent
        ORDER BY DATE(due_date) DESC, l.lease_id DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    out = []
    for lease_id, apartment, due_date, paid_amount, agreed_rent, status, is_late, payment_id in rows:
        payment_date = "-" if status == "Unpaid" else "Paid / Partial"
        out.append(
            (
                apartment,
                due_date,
                payment_date,
                round(float(paid_amount or 0), 2),
                round(float(agreed_rent or 0), 2),
                status,
                is_late or "No",
                int(payment_id or 0),
            )
        )
    return out


def get_all_payments():
    """Retrieves all payment records for Finance Manager."""
    update_late_status()

    conn = check_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.first_name || ' ' || u.surname as tenant_name,
               b.street || ' (' || b.postcode || ')' as apartment,
               loc.city_name,
               p.due_date,
               COALESCE(p.payment_date, '-') as payment_date,
               COALESCE(p.amount, 0) as paid_amount,
               l.Agreed_rent,
               CASE
                 WHEN p.payment_date IS NULL THEN 'Unpaid'
                 WHEN p.amount < l.Agreed_rent THEN 'Pending (Partial)'
                 ELSE 'Fully Paid'
               END as status,
               p.is_late,
               p.payment_id
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        JOIN Location loc ON b.city_id = loc.city_id
        ORDER BY p.due_date DESC, p.payment_id DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_payment_details(payment_id):
    """Fetch details for a single payment row."""
    update_late_status()

    conn = check_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.payment_id,
               u.first_name || ' ' || u.surname,
               ua.email,
               b.street,
               b.postcode,
               loc.city_name,
               p.due_date,
               COALESCE(p.payment_date, 'N/A'),
               COALESCE(p.amount, 0),
               l.Agreed_rent,
               p.is_late,
               CASE
                 WHEN p.payment_date IS NULL THEN 'Unpaid'
                 WHEN p.amount < l.Agreed_rent THEN 'Pending (Partial)'
                 ELSE 'Fully Paid'
               END as status
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        JOIN Location loc ON b.city_id = loc.city_id
        WHERE p.payment_id = ?
        """,
        (payment_id,),
    )

    r = cursor.fetchone()
    conn.close()

    if not r:
        return None

    return {
        "payment_id": r[0],
        "tenant_name": r[1],
        "tenant_email": r[2],
        "street": r[3],
        "postcode": r[4],
        "city": r[5],
        "due_date": r[6],
        "payment_date": r[7],
        "paid_amount": float(r[8] or 0),
        "agreed_rent": float(r[9] or 0),
        "is_late": r[10],
        "status": r[11],
        "property": f"{r[3]}, {r[4]}",
    }
