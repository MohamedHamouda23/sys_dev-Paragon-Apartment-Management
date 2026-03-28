import hashlib
import hmac
import secrets

from database.databaseConnection import check_connection
from .db_utils import execute_query, execute_transaction, get_user_city_id


# Password hashing constants
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 100000


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


def get_all_users(scope_city_id=None, exclude_user_id=None):
    query = """
        SELECT
            u.user_id,
            u.first_name,
            u.surname,
            ua.email,
            r.role_name
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        WHERE r.role_name != 'Tenant'
    """
    params = []

    if scope_city_id is not None:
        query += " AND u.city_id = ?"
        params.append(scope_city_id)

    if exclude_user_id is not None:
        query += " AND u.user_id != ?"
        params.append(exclude_user_id)

    query += " ORDER BY u.user_id ASC"
    return execute_query(query, tuple(params))


def get_all_roles():
    return execute_query("""
        SELECT role_id, role_name
        FROM Role
        WHERE role_name != 'Tenant'
        ORDER BY role_name ASC
    """)


def get_all_locations(scope_city_id=None):
    if scope_city_id is None:
        return execute_query("SELECT city_id, city_name FROM Location ORDER BY city_name ASC")
    else:
        return execute_query(
            "SELECT city_id, city_name FROM Location WHERE city_id = ? ORDER BY city_name ASC",
            (scope_city_id,)
        )


def create_user(first_name, surname, email, password_hash, role_id, city_id=None, scope_city_id=None):
    email = _validate_email(email)

    if scope_city_id is not None and city_id != scope_city_id:
        raise ValueError("Administrators can only create users in their assigned location.")

    # Check email uniqueness
    existing = execute_query("SELECT 1 FROM User_Access WHERE email = ?", (email,), 'one')
    if existing:
        raise ValueError("Email already exists.")

    # Create user and access records
    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")
    
    cursor = conn.cursor()
    try:
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
    finally:
        conn.close()


def update_user(user_id, first_name, surname, email, role_id, city_id=None, password_hash=None, scope_city_id=None):
    email = _validate_email(email)

    conn = check_connection()
    if conn is None:
        raise ValueError("Database connection failed.")

    cursor = conn.cursor()
    try:
        if scope_city_id is not None:
            user_row = execute_query("SELECT city_id FROM User WHERE user_id = ?", (user_id,), 'one')
            if user_row is None:
                raise ValueError("User not found.")
            if user_row[0] != scope_city_id:
                raise ValueError("Administrators can only update users in their assigned location.")
            if city_id != scope_city_id:
                raise ValueError("Administrators can only assign users to their own location.")

        # Check email uniqueness
        existing = execute_query(
            "SELECT 1 FROM User_Access WHERE email = ? AND user_id != ?",
            (email, user_id),
            'one'
        )
        if existing:
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
    finally:
        conn.close()


def delete_user(user_id, scope_city_id=None, acting_user_id=None, acting_role=None):
    # Prevent any user from deleting their own account
    if acting_user_id is not None and acting_user_id == user_id:
        raise ValueError("You cannot delete your own account.")

    email_row = execute_query("SELECT email FROM User_Access WHERE user_id = ?", (user_id,), 'one')
    if email_row is None:
        raise ValueError("User not found.")

    if scope_city_id is not None:
        user_row = execute_query("SELECT city_id FROM User WHERE user_id = ?", (user_id,), 'one')
        if user_row is None:
            raise ValueError("User not found.")
        if user_row[0] != scope_city_id:
            raise ValueError("Administrators can only delete users in their assigned location.")

    operations = [
        ("DELETE FROM User_Access WHERE user_id = ?", (user_id,)),
        ("DELETE FROM User WHERE user_id = ?", (user_id,))
    ]
    execute_transaction(operations)


def check_user(email, password):
    row = execute_query("""
        SELECT ua.password_hash, u.first_name, u.surname
        FROM User_Access ua
        JOIN User u ON u.user_id = ua.user_id
        WHERE ua.email = ?
    """, (email,), 'one')

    if not row:
        return None

    stored_password, first_name, surname = row
    return 1 if _verify_password(stored_password, password, first_name, surname) else None


def retrive_data(email, password=None):
    return execute_query("""
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
    """, (email,), 'one')


def get_login_debug_details(email):
    """Return minimal login debug info including stored password value."""
    return execute_query("""
        SELECT u.first_name, u.surname, r.role_name, ua.password_hash
        FROM User u
        JOIN User_Access ua ON u.user_id = ua.user_id
        JOIN Role r ON ua.role_id = r.role_id
        WHERE ua.email = ?
    """, (email,), 'one')