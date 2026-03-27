# tenant_portal_service.py
from datetime import datetime, timedelta
from database.databaseConnection import check_connection
from database.payment_service import update_late_status


def _fetch_one(query, params=()):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row


def _fetch_all(query, params=()):
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def ensure_tenant_portal_schema():
    conn = check_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Early_Termination_Request (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lease_id INTEGER NOT NULL,
            tenant_id INTEGER NOT NULL,
            request_date DATE NOT NULL,
            requested_move_out DATE NOT NULL,
            notice_days INTEGER NOT NULL,
            penalty_amount REAL NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lease_id) REFERENCES Lease(lease_id),
            FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id)
        )
        """
    )

    for stmt in [
        "ALTER TABLE Complaints ADD COLUMN category TEXT DEFAULT 'General'",
        "ALTER TABLE Complaints ADD COLUMN status TEXT DEFAULT 'Pending'",
        "ALTER TABLE Complaints ADD COLUMN resolution_update TEXT",
        "ALTER TABLE Complaints ADD COLUMN updated_at DATETIME",
    ]:
        try:
            cursor.execute(stmt)
        except Exception:
            pass

    conn.commit()
    conn.close()


def get_tenant_id_from_user(user_id):
    from database.databaseConnection import check_connection

    conn = check_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tenant_id
        FROM Tenant
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def get_active_lease_for_user(user_id):
    return _fetch_one(
        """
        SELECT
            l.lease_id,
            l.tenant_id,
            l.apartment_id,
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            a.type,
            b.street,
            b.postcode,
            loc.city_name
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        JOIN Location loc ON b.city_id = loc.city_id
        WHERE t.user_id = ?
        ORDER BY
            CASE
                WHEN DATE(l.end_date) >= DATE('now') THEN 0
                ELSE 1
            END,
            DATE(l.end_date) DESC
        LIMIT 1
        """,
        (user_id,),
    )


def get_tenant_profile(user_id):
    row = _fetch_one(
        """
        SELECT
            u.first_name,
            u.surname,
            ua.email,
            t.telephone,
            t.occupation,
            t.ni_number,
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            a.type,
            b.street,
            b.postcode,
            loc.city_name,
            t.tenant_id,
            l.lease_id
        FROM Tenant t
        JOIN User u ON t.user_id = u.user_id
        JOIN User_Access ua ON u.user_id = ua.user_id
        LEFT JOIN Lease l ON l.tenant_id = t.tenant_id
        LEFT JOIN Apartments a ON l.apartment_id = a.apartment_id
        LEFT JOIN Buildings b ON a.building_id = b.building_id
        LEFT JOIN Location loc ON b.city_id = loc.city_id
        WHERE t.user_id = ?
        ORDER BY DATE(l.end_date) DESC
        LIMIT 1
        """,
        (user_id,),
    )

    if not row:
        return None

    return {
        "name": f"{row[0]} {row[1]}",
        "email": row[2] or "",
        "phone": row[3] or "",
        "occupation": row[4] or "",
        "ni_number": row[5] or "",
        "lease_start": row[6],
        "lease_end": row[7],
        "monthly_rent": float(row[8]) if row[8] is not None else 0.0,
        "apartment_type": row[9] or "N/A",
        "location": f"{row[10] or ''}, {row[11] or ''}, {row[12] or ''}".strip(", "),
        "tenant_id": row[13],
        "lease_id": row[14],
    }


def get_tenant_payments_with_balance(user_id):
    """If payment_date is missing, status is 'Unpaid' and paid_amount is forced to 0.0."""
    update_late_status()
    rows = _fetch_all(
        """
        SELECT
            p.payment_id,
            p.lease_id,
            p.due_date,
            p.payment_date,
            COALESCE(p.amount, 0),
            l.Agreed_rent,
            COALESCE(p.is_late, 'No'),
            b.street,
            b.postcode,
            a.type,
            b.city_id
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE t.user_id = ?
          AND u.city_id = b.city_id
        ORDER BY DATE(p.due_date) DESC
        """,
        (user_id,),
    )

    out = []
    for r in rows:
        pay_date = r[3]
        paid = float(r[4] or 0) if pay_date else 0.0
        agreed = float(r[5] or 0)
        bal = agreed if not pay_date else max(agreed - paid, 0)

        if not pay_date:
            status = "Unpaid"
        elif paid < (agreed - 0.01):
            status = "Pending (Partial)"
        else:
            status = "Paid"

        out.append(
            {
                "payment_id": r[0],
                "lease_id": r[1],
                "due_date": r[2],
                "payment_date": pay_date if pay_date else "-",
                "paid_amount": paid,
                "agreed_rent": agreed,
                "outstanding": bal,
                "is_late": r[6] or "No",
                "status": status,
                "property": f"{r[7]} ({r[8]})",
                "apartment_type": r[9] or "N/A",
                "city_id": r[10],
            }
        )
    return out


def simulate_payment(user_id, payment_id, new_payment_amount):
    """
    Increments payment amount. 
    If previous record was 'Unpaid' (no date), initial amount is treated as 0.
    Sets payment_date to current date.
    """
    update_late_status()
    conn = check_connection()
    cursor = conn.cursor()

    # 1. Fetch current status
    cursor.execute(
        """
        SELECT COALESCE(p.amount, 0), l.Agreed_rent, p.due_date, p.payment_date
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE p.payment_id = ? AND t.user_id = ?
        """,
        (payment_id, user_id),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Payment record not found.")

    # Treat amount as 0 if no date was recorded previously
    current_paid = float(row[0]) if row[3] else 0.0
    agreed_rent = float(row[1])
    due_date = datetime.strptime(str(row[2]), "%Y-%m-%d").date()
    today = datetime.now().date()

    # 2. Calculate the new total (Current + Added)
    updated_total = round(current_paid + float(new_payment_amount), 2)
    
    # Validation: Don't allow overpaying
    if updated_total > agreed_rent + 0.01:
        conn.close()
        raise ValueError(f"Amount exceeds balance. Remaining: £{agreed_rent - current_paid:.2f}")

    # 3. Determine if late
    is_late = "Yes" if today > due_date and updated_total < (agreed_rent - 0.01) else "No"
    
    # 4. Update existing record with the payment date and new total
    cursor.execute(
        """
        UPDATE Payment
        SET payment_date = DATE('now'),
            amount = ?,
            is_late = ?
        WHERE payment_id = ?
        """,
        (updated_total, is_late, payment_id),
    )

    conn.commit()
    conn.close()
    return updated_total


def get_dashboard_metrics(user_id):
    payments = get_tenant_payments_with_balance(user_id)
    total_paid = round(sum(p["paid_amount"] for p in payments), 2)
    total_due = round(sum(p["agreed_rent"] for p in payments), 2)
    outstanding = round(sum(p["outstanding"] for p in payments), 2)
    late_count = sum(1 for p in payments if str(p["is_late"]).lower() == "yes")

    alerts = []
    if late_count > 0:
        alerts.append("Payment overdue")
        alerts.append("Late fee applied (if applicable)")

    return {
        "total_paid": total_paid,
        "total_due": total_due,
        "outstanding": outstanding,
        "late_count": late_count,
        "alerts": alerts,
    }


def get_payment_history_series(user_id):
    # Sum only where a payment_date exists to avoid counting phantom amounts
    rows = _fetch_all(
        """
        SELECT strftime('%Y-%m', due_date) AS ym, SUM(COALESCE(amount, 0))
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.user_id = ? AND p.payment_date IS NOT NULL
        GROUP BY ym
        ORDER BY ym
        """,
        (user_id,),
    )
    return [(r[0], float(r[1] or 0)) for r in rows]


def get_late_payment_by_property(user_id):
    update_late_status()
    rows = _fetch_all(
        """
        SELECT
            b.postcode,
            SUM(CASE WHEN COALESCE(p.is_late, 'No') = 'Yes' THEN 1 ELSE 0 END) AS late_count
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE t.user_id = ?
        GROUP BY b.postcode
        ORDER BY late_count DESC
        """,
        (user_id,),
    )
    return [(r[0], int(r[1] or 0)) for r in rows]


def get_neighbor_comparison(user_id):
    tenant_row = _fetch_one(
        """
        SELECT
            COALESCE(AVG(p.amount), 0),
            a.type,
            b.city_id
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE t.user_id = ? AND p.payment_date IS NOT NULL
        """,
        (user_id,),
    )

    if not tenant_row:
        return {"tenant_avg": 0.0, "neighbor_avg": 0.0, "group": "N/A"}

    tenant_avg = float(tenant_row[0] or 0)
    apt_type = tenant_row[1]
    city_id = tenant_row[2]

    neighbor_row = _fetch_one(
        """
        SELECT COALESCE(AVG(p.amount), 0)
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        WHERE a.type = ?
          AND b.city_id = ?
          AND t.user_id != ?
          AND p.payment_date IS NOT NULL
        """,
        (apt_type, city_id, user_id),
    )

    neighbor_avg = float(neighbor_row[0] or 0)
    return {
        "tenant_avg": tenant_avg,
        "neighbor_avg": neighbor_avg,
        "group": f"{apt_type} / same city",
    }


def get_tenant_maintenance_requests(user_id):
    rows = _fetch_all(
        """
        SELECT
            mr.request_id,
            COALESCE(mr.issue, ''),
            COALESCE(mr.description, ''),
            DATE(mr.created_date),
            mr.Maintenance_status,
            COALESCE(e.Full_name, '')
        FROM Maintenance_Request mr
        JOIN Tenant t ON mr.tenant_id = t.tenant_id
        LEFT JOIN Maintenance_Assignment ma ON mr.request_id = ma.request_id AND ma.is_current = 1
        LEFT JOIN Employee e ON ma.employee_id = e.employee_id
        WHERE t.user_id = ?
        ORDER BY mr.created_date DESC
        """,
        (user_id,),
    )
    return rows


def submit_tenant_maintenance_request(user_id, category, description):
    lease = get_active_lease_for_user(user_id)
    if not lease:
        raise ValueError("No active lease found for tenant.")

    apartment_id = lease[2]
    tenant_id = lease[1]

    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Maintenance_Request
        (apartment_id, tenant_id, issue, description, Maintenance_status, priority, created_date)
        VALUES (?, ?, ?, ?, 'Open', 'Medium', ?)
        """,
        (apartment_id, tenant_id, category, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_tenant_complaints(user_id):
    tenant_id = get_tenant_id_from_user(user_id)
    if not tenant_id:
        return []
    
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT complaint_id, description, date_submitted 
        FROM Complaints 
        WHERE tenant_id = ?
        ORDER BY date_submitted DESC
    """, (tenant_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows


def submit_tenant_complaint(user_id, description):
    tenant_id = get_tenant_id_from_user(user_id)
    if not tenant_id:
        raise ValueError("Tenant not found for this user")
    
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Complaints (tenant_id, description, date_submitted) 
        VALUES (?, ?, DATE('now'))
    """, (tenant_id, description))
    
    conn.commit()
    conn.close()


def get_notifications(user_id):
    update_late_status()
    notes = []

    upcoming = _fetch_all(
        """
        SELECT due_date
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.user_id = ?
          AND (p.payment_date IS NULL)
          AND DATE(p.due_date) BETWEEN DATE('now') AND DATE('now', '+7 day')
        ORDER BY DATE(p.due_date)
        """,
        (user_id,),
    )
    for r in upcoming:
        notes.append(f"Upcoming rent due date: {r[0]}")

    late_rows = _fetch_all(
        """
        SELECT due_date
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.user_id = ? AND COALESCE(p.is_late, 'No') = 'Yes'
        ORDER BY DATE(p.due_date) DESC
        LIMIT 3
        """,
        (user_id,),
    )
    if late_rows:
        notes.append("Late payments detected on your account.")

    maint = _fetch_all(
        """
        SELECT request_id, Maintenance_status
        FROM Maintenance_Request mr
        JOIN Tenant t ON mr.tenant_id = t.tenant_id
        WHERE t.user_id = ?
        ORDER BY mr.created_date DESC
        LIMIT 3
        """,
        (user_id,),
    )
    for req_id, st in maint:
        notes.append(f"Maintenance update for request #{req_id}: {st}")

    comp = _fetch_all(
        """
        SELECT complaint_id, 'Submitted' 
        FROM Complaints c
        JOIN Tenant t ON c.tenant_id = t.tenant_id
        WHERE t.user_id = ?
        ORDER BY complaint_id DESC
        LIMIT 3
        """,
        (user_id,),
    )
    for comp_id, st in comp:
        notes.append(f"Complaint #{comp_id} status: {st}")

    return notes


def get_late_payment_notifications(user_id):
    update_late_status()
    rows = _fetch_all(
        """
        SELECT due_date
        FROM Payment p
        JOIN Lease l ON p.lease_id = l.lease_id
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        WHERE t.user_id = ?
          AND COALESCE(p.is_late, 'No') = 'Yes'
        ORDER BY DATE(p.due_date) DESC
        """,
        (user_id,),
    )

    if not rows:
        return ["No late payments"]

    return [f"Late payment overdue (due date: {r[0]})" for r in rows]


def submit_early_termination_request(user_id, requested_move_out, reason):
    ensure_tenant_portal_schema()
    lease = get_active_lease_for_user(user_id)
    if not lease:
        raise ValueError("No lease found for this tenant.")

    lease_id, tenant_id, _, _, _, monthly_rent, *_ = lease

    try:
        move_out_date = datetime.strptime(requested_move_out, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Move-out date must be in YYYY-MM-DD format.")

    today = datetime.now().date()
    notice_days = (move_out_date - today).days
    if notice_days < 30:
        raise ValueError("Early termination requires at least 1 month notice.")

    penalty = round(float(monthly_rent or 0) * 0.05, 2)

    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Early_Termination_Request
        (lease_id, tenant_id, request_date, requested_move_out, notice_days, penalty_amount, reason, status)
        VALUES (?, ?, DATE('now'), ?, ?, ?, ?, 'Pending')
        """,
        (lease_id, tenant_id, requested_move_out, notice_days, penalty, reason),
    )
    conn.commit()
    conn.close()

    return penalty


def get_early_termination_requests(user_id):
    ensure_tenant_portal_schema()
    return _fetch_all(
        """
        SELECT request_id, request_date, requested_move_out, notice_days, penalty_amount, status
        FROM Early_Termination_Request etr
        JOIN Tenant t ON etr.tenant_id = t.tenant_id
        WHERE t.user_id = ?
        ORDER BY request_id DESC
        """,
        (user_id,),
    )