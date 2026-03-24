# ============================================================================
# PAYMENT SERVICE
# Database operations for payment management
# ============================================================================

from database.db_connection import get_connection


def get_all_payments():
    """Get all payments across all cities (Finance Manager)."""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                p.payment_id,
                p.lease_id,
                COALESCE(u.first_name || ' ' || u.last_name, 'N/A') AS tenant_name,
                COALESCE(a.apartment_name, 'N/A') AS apartment,
                COALESCE(c.city_name, 'N/A') AS city,
                p.due_date,
                p.payment_date,
                p.amount,
                p.status,
                CASE WHEN p.is_late = 1 THEN 'Yes' ELSE 'No' END AS is_late
            FROM payments p
            LEFT JOIN leases l ON p.lease_id = l.lease_id
            LEFT JOIN users u ON l.tenant_id = u.user_id
            LEFT JOIN apartments a ON l.apartment_id = a.apartment_id
            LEFT JOIN buildings b ON a.building_id = b.building_id
            LEFT JOIN cities c ON b.city_id = c.city_id
            ORDER BY p.due_date DESC, p.payment_id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error fetching all payments: {e}")
        return []
    finally:
        conn.close()


def get_payments_by_city(city_id):
    """Get payments for a specific city (Coordinator)."""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                p.payment_id,
                p.lease_id,
                COALESCE(u.first_name || ' ' || u.last_name, 'N/A') AS tenant_name,
                COALESCE(a.apartment_name, 'N/A') AS apartment,
                COALESCE(c.city_name, 'N/A') AS city,
                p.due_date,
                p.payment_date,
                p.amount,
                p.status,
                CASE WHEN p.is_late = 1 THEN 'Yes' ELSE 'No' END AS is_late
            FROM payments p
            LEFT JOIN leases l ON p.lease_id = l.lease_id
            LEFT JOIN users u ON l.tenant_id = u.user_id
            LEFT JOIN apartments a ON l.apartment_id = a.apartment_id
            LEFT JOIN buildings b ON a.building_id = b.building_id
            LEFT JOIN cities c ON b.city_id = c.city_id
            WHERE c.city_id = ?
            ORDER BY p.due_date DESC, p.payment_id DESC
        """
        cursor.execute(query, (city_id,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error fetching payments by city: {e}")
        return []
    finally:
        conn.close()