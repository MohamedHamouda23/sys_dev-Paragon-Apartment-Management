# ============================================================================
# VALIDATION UTILITIES
# Centralized validation functions for all management modules
# ============================================================================

import re
from tkinter import messagebox
from datetime import datetime


# ============================================================================
# SHARED VALIDATIONS
# ============================================================================

def validate_required_fields(fields_dict, empty_message=None):
    """Validate that required fields are not empty."""
    for field_name, value in fields_dict.items():
        if value in (None, "") or not str(value).strip():
            if empty_message:
                raise ValueError(empty_message)
            raise ValueError(f"{field_name} is required.")


def validate_positive_number(value, field_name):
    """Validate that a value is a positive number and return it as float."""
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid number.")

    if num <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")

    return num


def validate_email_address(email, required=True):
    """Validate email format and return normalized value."""
    normalized = (email or "").strip()

    if required and not normalized:
        raise ValueError("Email is required.")

    if normalized and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise ValueError("Email format is invalid. Use name@example.com.")

    return normalized


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
    OCCUPANCY = ['Vacant', 'Unavailable']
    
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
# MAINTENANCE REQUEST VALIDATIONS
# ============================================================================

def validate_request_form(tenant_name, apt_label, issue, priority, require_priority=True):
    """Validate maintenance request form data"""
    errors = []
    
    # Check required fields
    if not tenant_name or not tenant_name.strip():
        errors.append("• Please select a tenant")
    
    if not apt_label or not apt_label.strip():
        errors.append("• Please select an apartment")
    
    if not issue or not issue.strip():
        errors.append("• Issue description is required")
    elif len(issue.strip()) < 5:
        errors.append("• Issue description must be at least 5 characters")
    
    # Validate priority when required
    if require_priority and priority not in ["High", "Medium", "Low"]:
        errors.append("• Please select a valid priority")
    
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


def validate_staff_assignment(staff_name, priority, date_str, selected_slot, comment, require_staff=True, require_priority=True):
    """Validate staff assignment and scheduling form inputs"""
    errors = []
    
    # Check required fields
    if require_staff and not staff_name:
        errors.append("• Select staff member")
    
    if require_priority and not priority:
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


# ============================================================================
# TENANT VALIDATIONS
# ============================================================================

def validate_phone_number(phone_number, field_name="Telephone"):
    """Validate phone number as 6-15 digits (spaces and dashes are ignored)."""
    if not phone_number or not str(phone_number).strip():
        raise ValueError(
            f"{field_name} is required. Format: 6-15 digits, optional +, spaces and dashes allowed (e.g. +44 7700 900123)."
        )

    cleaned = re.sub(r"[\s\-\(\)]", "", str(phone_number).strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    if not cleaned.isdigit() or len(cleaned) < 6 or len(cleaned) > 15:
        raise ValueError(
            f"{field_name} format is invalid. Use 6-15 digits, optional +, spaces and dashes allowed (e.g. +44 7700 900123)."
        )

    return True


def validate_national_insurance_number(ni_number):
    """Validate UK National Insurance number format."""
    if not ni_number or not str(ni_number).strip():
        raise ValueError("National Insurance Number is required. Format: QQ123456C or QQ 12 34 56 C.")

    # Accepts with or without spaces, e.g. QQ123456C or QQ 12 34 56 C.
    # This keeps the required structure (2 letters, 6 digits, 1 letter)
    # while avoiding over-restrictive prefix/suffix rules.
    ni = str(ni_number).strip().upper()
    pattern = re.compile(r"^[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-Z]$")
    if not pattern.fullmatch(ni):
        raise ValueError("National Insurance Number format is invalid. Use QQ123456C or QQ 12 34 56 C.")

    return True


def validate_tenant_form(data):
    """Validate tenant form payload and raise one combined error message when invalid."""
    first_name, surname, email, telephone, reference_name, reference_email, ni_number, _, _, occupation = data

    validate_required_fields(
        {
            "First Name": first_name,
            "Surname": surname,
            "Email": email,
            "Telephone": telephone,
            "National Insurance Number": ni_number,
            "Occupation": occupation,
        },
        empty_message="There is an empty field. Please fill in all required fields.",
    )

    errors = []

    if not re.fullmatch(r"[A-Za-z][A-Za-z\s'-]{0,79}", first_name):
        errors.append("- First Name format: letters, spaces, apostrophes or hyphens only (example: John or Anne-Marie).")

    if not re.fullmatch(r"[A-Za-z][A-Za-z\s'-]{0,79}", surname):
        errors.append("- Surname format: letters, spaces, apostrophes or hyphens only (example: O'Connor).")

    try:
        validate_email_address(email)
    except ValueError:
        errors.append("- Email format: use name@example.com.")

    try:
        validate_phone_number(telephone)
    except ValueError:
        errors.append("- Telephone format: 6-15 digits (optional +, spaces and dashes allowed), e.g. +44 7700 900123.")

    if reference_name and not re.fullmatch(r"[A-Za-z][A-Za-z\s'-]{0,119}", reference_name):
        errors.append("- Reference Name format: letters, spaces, apostrophes or hyphens only.")

    if reference_email:
        try:
            validate_email_address(reference_email)
        except ValueError:
            errors.append("- Reference Email format: use name@example.com.")

    try:
        validate_national_insurance_number(ni_number)
    except ValueError:
        errors.append("- National Insurance Number format: use QQ123456C or QQ 12 34 56 C.")

    if errors:
        raise ValueError("Please correct the following:\n" + "\n".join(errors))

    return True