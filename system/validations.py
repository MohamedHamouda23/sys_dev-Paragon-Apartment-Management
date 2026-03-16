# ============================================================================
# VALIDATION UTILITIES
# Centralized validation functions for all management modules
# ============================================================================

import re
from tkinter import messagebox
from datetime import datetime



# ============================================================================
# USER VALIDATIONS
# ============================================================================

def validate_user_form(first_name, surname, email, role_name, require_password=False, password=""):
    """Validate user form inputs"""
    errors = []
    
    # Check required fields
    if not first_name:
        errors.append("• First name is required")
    if not surname:
        errors.append("• Surname is required")
    if not email:
        errors.append("• Email is required")
    if not role_name:
        errors.append("• Role is required")
    if require_password and not password:
        errors.append("• Password is required")
    
    # Validate email format
    if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        errors.append("• Invalid email format")
    
    # Validate names (only letters and spaces)
    if first_name and not re.match(r'^[A-Za-z\s]+$', first_name):
        errors.append("• First name must contain only letters")
    if surname and not re.match(r'^[A-Za-z\s]+$', surname):
        errors.append("• Surname must contain only letters")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


# ============================================================================
# PROPERTY VALIDATIONS
# ============================================================================

def validate_city_name(city_name):
    """Validate city name (only letters allowed)"""
    if not city_name:
        raise ValueError("City name is required")
    if not city_name.isalpha():
        raise ValueError("City names must only contain letters")
    return True


def validate_building_form(city, street, postcode):
    """Validate building form inputs"""
    errors = []
    
    # Check required fields
    if not city:
        errors.append("• City is required")
    if not street:
        errors.append("• Street is required")
    if not postcode:
        errors.append("• Postcode is required")
    
    # Validate postcode
    if postcode:
        if " " in postcode:
            errors.append("• Postcode cannot contain spaces")
        elif not postcode.isalnum():
            errors.append("• Postcode must contain letters and numbers only")
        elif len(postcode) != 7:
            errors.append("• Postcode must be exactly 7 characters")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


def validate_apartment_form(rooms, apt_type, occ):
    """Validate apartment form inputs"""
    TYPES = ['Studio', 'Apartment', 'Penthouse']
    OCCUPANCY = ['Occupied', 'Vacant', 'Unavailable']
    
    errors = []
    
    # Check required fields
    if not rooms:
        errors.append("• Number of Rooms is required")
    if not apt_type:
        errors.append("• Property Type is required")
    if not occ:
        errors.append("• Occupancy Status is required")
    
    # Validate rooms
    if rooms and (not rooms.isdigit() or int(rooms) <= 0):
        errors.append("• Number of Rooms must be a positive number")
    
    # Validate type
    if apt_type and apt_type not in TYPES:
        errors.append("• Please select a valid Property Type")
    
    # Validate occupancy
    if occ and occ not in OCCUPANCY:
        errors.append("• Please select a valid Occupancy Status")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


# ============================================================================
# LEASE VALIDATIONS
# ============================================================================

def validate_lease_selection(tenant_name, apt_display):
    """Validate lease selections"""
    if not tenant_name:
        raise ValueError("Please select a tenant")
    if not apt_display:
        raise ValueError("Please select an apartment")
    return True


def validate_lease_details(start_date, end_date, rent):
    """Validate lease detail inputs"""
    errors = []
    
    if not start_date:
        errors.append("• Start date is required")
    if not end_date:
        errors.append("• End date is required")
    if not rent:
        errors.append("• Monthly rent is required")
    
    # Validate rent is numeric
    if rent:
        try:
            float(rent)
        except ValueError:
            errors.append("• Monthly rent must be a valid number")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


# ============================================================================
# REQUEST VALIDATIONS
# ============================================================================


def validate_staff_assignment(staff_name, priority, date_str, selected_slot, comment):
    """Validate staff assignment and scheduling form inputs"""
    errors = []
    
    # Check required fields
    if not staff_name:
        errors.append("• Select staff member")
    
    if not priority:
        errors.append("• Select priority")
    
    if not date_str:
        errors.append("• Date is required")
    elif not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        errors.append("• Valid date required (YYYY-MM-DD)")
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append("• Invalid date")
    
    if not selected_slot:
        errors.append("• Please select an available time slot")
    
    if not comment or not comment.strip():
        errors.append("• Assignment description is required")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


def validate_resolution_form(notes, repair_time, repair_cost):
    """Validate resolution form inputs"""
    errors = []
    
    if not notes or not notes.strip():
        errors.append("• Resolution notes are required")
    
    # Validate numeric fields
    if repair_time:
        try:
            time_val = float(repair_time)
            if time_val < 0:
                errors.append("• Repair time cannot be negative")
        except ValueError:
            errors.append("• Repair time must be a valid number")
    
    if repair_cost:
        try:
            cost_val = float(repair_cost)
            if cost_val < 0:
                errors.append("• Repair cost cannot be negative")
        except ValueError:
            errors.append("• Repair cost must be a valid number")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True


def validate_maintenance_request(apartment_id, tenant_id, issue, priority):
    """Validate new maintenance request form"""
    errors = []
    
    if not apartment_id:
        errors.append("• Please select an apartment")
    
    if not tenant_id:
        errors.append("• Please select a tenant")
    
    if not issue or not issue.strip():
        errors.append("• Issue description is required")
    
    if not priority:
        errors.append("• Please select a priority")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True