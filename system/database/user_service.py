import hashlib
import hmac
import secrets

from database.databaseConnection import check_connection, fetch_all, insert


PROTECTED_ADMIN_EMAILS = {
    "bristol_admin@company.com",
    "cardiff_admin@company.com",
    "london_admin@company.com",
    "manchester_admin@company.com",
}

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 120000


def _validate_email(email):
    normalized = (email or "").strip()
    if "@" not in normalized:
        raise ValueError("Email must contain '@'.")
    return normalized


def _name_key(first_name, surname):
    """Build a deterministic key material from user name fields."""
    first = (first_name or "").strip().lower()
    last = (surname or "").strip().lower()
    return f"{first}:{last}".encode("utf-8")


def _hash_password_with_name_key(password_plain, first_name, surname):
    """Hash password with random salt and name-derived key material."""
    if password_plain is None:
        raise ValueError("Password is required.")

    password_bytes = str(password_plain).encode("utf-8")
    salt = secrets.token_bytes(16)
    name_material = _name_key(first_name, surname)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt + name_material,
        PASSWORD_ITERATIONS,
    )
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(stored_password, password_plain, first_name, surname):
    """Verify both new hashed format and legacy plaintext passwords."""
    if stored_password is None:
        return False

    parts = str(stored_password).split("$")
    if len(parts) == 4 and parts[0] == PASSWORD_SCHEME:
        try:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            stored_digest = bytes.fromhex(parts[3])
        except (ValueError, TypeError):
            return False

        computed = hashlib.pbkdf2_hmac(
            "sha256",
            str(password_plain).encode("utf-8"),
            salt + _name_key(first_name, surname),
            iterations,
        )
        return hmac.compare_digest(computed, stored_digest)

    # Backward compatibility for existing demo records stored in plaintext.
    return str(stored_password) == str(password_plain)


def get_all_users(scope_city_id=None):
    conn = check_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    query = """
        SELECT
            u.user_id,
            u.first_name,
            u.surname,
            ua.email,
            COALESCE(l.city_name, ''),
            r.role_name
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        LEFT JOIN Location l ON u.city_id = l.city_id
        JOIN Role r ON ua.role_id = r.role_id
        WHERE r.role_name != 'Tenant'
    """
    params = []

    if scope_city_id is not None:
        query += " AND u.city_id = ?"
        params.append(scope_city_id)

    query += " ORDER BY u.user_id ASC"
    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()
    return users


def get_all_roles():
    conn = check_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT role_id, role_name
        FROM Role
        WHERE role_name != 'Tenant'
        ORDER BY role_name ASC
    """)
    roles = cursor.fetchall()
    conn.close()
    return roles


def get_all_locations(scope_city_id=None):
    conn = check_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    if scope_city_id is None:
        cursor.execute("SELECT city_id, city_name FROM Location ORDER BY city_name ASC")
    else:
        cursor.execute(
            "SELECT city_id, city_name FROM Location WHERE city_id = ? ORDER BY city_name ASC",
            (scope_city_id,)
        )
    cities = cursor.fetchall()
    conn.close()
    return cities


def create_user(first_name, surname, email, password_hash, role_id, city_id=None, scope_city_id=None):
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    email = _validate_email(email)

    if scope_city_id is not None and city_id != scope_city_id:
        conn.close()
        raise ValueError("Administrators can only create users in their assigned location.")

    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM User_Access WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email already exists.")

    cursor.execute(
        "INSERT INTO User (city_id, first_name, surname) VALUES (?, ?, ?)",
        (city_id, first_name, surname)
    )
    new_user_id = cursor.lastrowid

    stored_password = _hash_password_with_name_key(password_hash, first_name, surname)

    cursor.execute(
        "INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES (?, ?, ?, ?)",
        (new_user_id, stored_password, role_id, email)
    )
    conn.commit()
    conn.close()


def update_user(user_id, first_name, surname, email, role_id, city_id=None, password_hash=None, scope_city_id=None):
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    email = _validate_email(email)

    cursor = conn.cursor()

    if scope_city_id is not None:
        cursor.execute("SELECT city_id FROM User WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if user_row is None:
            conn.close()
            raise ValueError("User not found.")
        if user_row[0] != scope_city_id:
            conn.close()
            raise ValueError("Administrators can only update users in their assigned location.")
        if city_id != scope_city_id:
            conn.close()
            raise ValueError("Administrators can only assign users to their own location.")

    cursor.execute(
        "SELECT 1 FROM User_Access WHERE email = ? AND user_id != ?",
        (email, user_id)
    )
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email already exists.")

    cursor.execute(
        "UPDATE User SET city_id = ?, first_name = ?, surname = ? WHERE user_id = ?",
        (city_id, first_name, surname, user_id)
    )

    if password_hash:
        stored_password = _hash_password_with_name_key(password_hash, first_name, surname)
        cursor.execute(
            "UPDATE User_Access SET email = ?, role_id = ?, password_hash = ? WHERE user_id = ?",
            (email, role_id, stored_password, user_id)
        )
    else:
        cursor.execute(
            "UPDATE User_Access SET email = ?, role_id = ? WHERE user_id = ?",
            (email, role_id, user_id)
        )

    conn.commit()
    conn.close()


def delete_user(user_id, scope_city_id=None, acting_user_id=None, acting_role=None):
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    cursor = conn.cursor()

    if acting_role == "Administrators" and acting_user_id == user_id:
        conn.close()
        raise ValueError("Administrators cannot delete their own account.")

    cursor.execute("SELECT email FROM User_Access WHERE user_id = ?", (user_id,))
    email_row = cursor.fetchone()
    if email_row is None:
        conn.close()
        raise ValueError("User not found.")

    target_email = email_row[0]
    if target_email in PROTECTED_ADMIN_EMAILS:
        conn.close()
        raise ValueError("This branch administrator account is permanent and cannot be deleted.")

    if scope_city_id is not None:
        cursor.execute("SELECT city_id FROM User WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if user_row is None:
            conn.close()
            raise ValueError("User not found.")
        if user_row[0] != scope_city_id:
            conn.close()
            raise ValueError("Administrators can only delete users in their assigned location.")

    cursor.execute("DELETE FROM User_Access WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM User WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def check_user(email, password):
       
    conn = check_connection()

    if conn is None:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ua.password_hash, u.first_name, u.surname
        FROM User_Access ua
        JOIN User u ON u.user_id = ua.user_id
        WHERE ua.email = ?
    """, (email,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    stored_password, first_name, surname = row
    return 1 if _verify_password(stored_password, password, first_name, surname) else None

def retrive_data(email, password=None):
    
    conn = check_connection()
    if conn is None:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.user_id,
            u.first_name,
            u.surname,
            l.city_name,
            r.role_name,
            u.city_id
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        JOIN Location l ON u.city_id = l.city_id
        WHERE ua.email = ?
    """, (email,))

    user_data = cursor.fetchone()
    conn.close()
    return user_data


def get_login_debug_details(email):
    """Return minimal login debug info including stored password value."""
    conn = check_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.first_name, u.surname, r.role_name, ua.password_hash
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        WHERE ua.email = ?
    """, (email,))
    details = cursor.fetchone()
    conn.close()
    return details
