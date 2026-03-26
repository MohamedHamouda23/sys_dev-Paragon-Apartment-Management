# payment_service.py
from database.databaseConnection import check_connection

def update_late_status():
    """Updates the 'is_late' column in Payment table based on current date and payment status."""
    conn = check_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Payment
        SET is_late = CASE
            WHEN date(due_date) < date('now') 
                 AND (payment_date IS NULL OR amount < (SELECT Agreed_rent FROM Lease WHERE Lease.lease_id = Payment.lease_id))
            THEN 'Yes'
            ELSE 'No'
        END
    """)
    conn.commit()
    conn.close()


def get_tenant_payments(user_id):
    """Retrieves payments for a specific tenant, updating late payments first."""
    update_late_status()  # auto-update late payments
    
    conn = check_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.street || ' (' || b.postcode || ')' as apartment,
               p.due_date, 
               COALESCE(p.payment_date, '-') as payment_date,
               COALESCE(p.amount, 0) as paid_amount, 
               l.Agreed_rent,
               CASE 
                 WHEN p.payment_date IS NULL OR p.amount IS NULL OR p.amount = 0 THEN 'Unpaid'
                 WHEN p.amount < l.Agreed_rent THEN 'Pending (Partial)'
                 ELSE 'Fully Paid' 
               END as status,
               p.is_late,
               p.payment_id
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE t.user_id = ? 
        ORDER BY p.due_date DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_payments():
    """Retrieves all payments for the Finance Manager, updating late payments first."""
    update_late_status()  # auto-update late payments

    conn = check_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.first_name || ' ' || u.surname as tenant_name,
               b.street || ' (' || b.postcode || ')' as apartment,
               loc.city_name, 
               p.due_date, 
               COALESCE(p.payment_date, '-') as payment_date,
               COALESCE(p.amount, 0) as paid_amount, 
               l.Agreed_rent,
               CASE 
                 WHEN p.payment_date IS NULL OR p.amount IS NULL OR p.amount = 0 THEN 'Unpaid'
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
        ORDER BY p.due_date DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_payment_details(payment_id):
    """Fetch details of a single payment, with late status updated."""
    update_late_status()  # auto-update late payments

    conn = check_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("""
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
                 WHEN p.payment_date IS NULL OR p.amount IS NULL OR p.amount = 0 THEN 'Unpaid'
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
    """, (payment_id,))

    r = cursor.fetchone()
    conn.close()

    if r:
        return {
            'payment_id': r[0],
            'tenant_name': r[1],
            'tenant_email': r[2],
            'street': r[3],
            'postcode': r[4],
            'city': r[5],
            'due_date': r[6],
            'payment_date': r[7],
            'paid_amount': float(r[8]),
            'agreed_rent': float(r[9]),
            'is_late': r[10],
            'status': r[11],
            'property': f"{r[3]}, {r[4]}"
        }

    return None