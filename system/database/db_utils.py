"""
Database Utilities Module
Shared helper functions to eliminate code repetition across service modules.
"""

from database.databaseConnection import check_connection


# ============================================================================
# QUERY EXECUTION HELPERS
# ============================================================================

def execute_query(query, params=(), fetch_mode='all'):
    """
    Execute a query and return results based on fetch_mode.
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_mode: 'all', 'one', or 'none' (for INSERT/UPDATE/DELETE)
    
    Returns:
        Query results or None
    """
    conn = check_connection()
    if conn is None:
        return [] if fetch_mode == 'all' else None
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    if fetch_mode == 'all':
        result = cursor.fetchall()
    elif fetch_mode == 'one':
        result = cursor.fetchone()
    else:  # 'none' - for writes
        conn.commit()
        result = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
    
    conn.close()
    return result


def execute_transaction(operations):
    """
    Execute multiple operations in a single transaction.
    
    Args:
        operations: List of (query, params) tuples
    
    Returns:
        True on success, False on failure
    """
    conn = check_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    try:
        for query, params in operations:
            cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Transaction error: {e}")
        return False
    finally:
        conn.close()


# ============================================================================
# ROLE CHECKING HELPERS
# ============================================================================

def is_manager(user_info):
    """Check if user has Manager role."""
    return user_info and len(user_info) > 4 and user_info[4] == "Manager"


def is_tenant(user_info):
    """Check if user has Tenant role."""
    return user_info and len(user_info) > 4 and user_info[4] == "Tenant"


def get_user_city_id(user_info):
    """Extract city_id from user_info tuple."""
    return user_info[5] if user_info and len(user_info) > 5 else None


def get_user_id(user_info):
    """Extract user_id from user_info tuple."""
    return user_info[0] if user_info and len(user_info) > 0 else None


# ============================================================================
# QUERY BUILDING HELPERS
# ============================================================================

def build_city_filter(base_query, city_id_column, user_info=None, selected_city_name=None):
    """
    Build city filter for queries based on user role.
    
    Args:
        base_query: Base SQL query string
        city_id_column: Column name for city filtering (e.g., 'b.city_id', 'a.city_id')
        user_info: User info tuple
        selected_city_name: Optional city name for manager filtering
    
    Returns:
        (query_with_where, params_tuple)
    """
    params = []
    where_clauses = []
    
    # Managers can see all cities or filter by name
    if is_manager(user_info):
        if selected_city_name and selected_city_name != "All Cities":
            where_clauses.append("l.city_name = ?")
            params.append(selected_city_name)
    else:
        # Non-managers: filter by assigned city
        city_id = get_user_city_id(user_info)
        if city_id is not None:
            where_clauses.append(f"{city_id_column} = ?")
            params.append(city_id)
    
    query = base_query
    if where_clauses:
        # Check if query already has WHERE clause
        if 'WHERE' in query.upper():
            query += " AND " + " AND ".join(where_clauses)
        else:
            query += " WHERE " + " AND ".join(where_clauses)
    
    return query, tuple(params)


def add_where_clauses(base_query, clauses_dict):
    """
    Add multiple WHERE clauses to a query.
    
    Args:
        base_query: Base SQL query
        clauses_dict: Dict of {column: value} for WHERE clauses
    
    Returns:
        (query, params_tuple)
    """
    if not clauses_dict:
        return base_query, ()
    
    params = []
    clauses = []
    
    for column, value in clauses_dict.items():
        if value is not None:
            clauses.append(f"{column} = ?")
            params.append(value)
    
    if clauses:
        separator = " AND " if "WHERE" in base_query.upper() else " WHERE "
        query = base_query + separator + " AND ".join(clauses)
    else:
        query = base_query
    
    return query, tuple(params)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_required_fields(fields_dict):
    """
    Validate that required fields are not empty.
    
    Args:
        fields_dict: Dict of {field_name: value}
    
    Raises:
        ValueError if any field is empty
    """
    for field_name, value in fields_dict.items():
        if value in (None, "") or not str(value).strip():
            raise ValueError(f"{field_name} is required.")


def validate_positive_number(value, field_name):
    """Validate that a value is a positive number."""
    try:
        num = float(value)
        if num <= 0:
            raise ValueError(f"{field_name} must be greater than 0.")
        return num
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number.")