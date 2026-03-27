# ============================================================================
# USER MANAGEMENT MODULE
# Handles user form creation and validation
# ============================================================================

import tkinter as tk
from tkinter import ttk

from main.helpers import (
    create_button, clear_frame, styled_label,
    form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE, FONT_LABEL,
)
from validations import validate_user_form


# ============================================================================
# USER FORM STEPPER CLASS
# ============================================================================

class UserFormStepper:
    """Multi-step form for creating/editing users"""

    def __init__(self, parent, role_name_to_id, prefill=None):
        # Store parent and lookup dictionaries
        self.parent          = parent
        self.role_name_to_id = role_name_to_id
        self._prefill        = prefill

        # Initialize widget references
        self.first_name_entry = None
        self.surname_entry    = None
        self.email_entry      = None
        self.password_entry   = None
        self.role_combobox    = None

        # Defer rendering to avoid macOS autorelease crash
        self.parent.after(0, lambda: self._do_render(prefill))

    # ========================================================================
    # RENDER METHODS
    # ========================================================================

    def _render_form(self, prefill=None):
        """Public entry point for rendering"""
        self._prefill = prefill
        self.parent.after(0, lambda: self._do_render(prefill))

    def _do_render(self, prefill=None):
        """Build form widgets on main loop tick"""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Create main form container
        form = tk.Frame(self.parent, bg="white")
        form.pack(fill="x", padx=16, pady=(10, 10))

        # Create text input fields
        self.first_name_entry = self._field(form, "First Name", 0, 0)
        self.surname_entry    = self._field(form, "Surname",    0, 2)
        self.email_entry      = self._field(form, "Email",      1, 0)
        self.password_entry   = self._field(form, "Password",   1, 2, show="*")

        # Create dropdown fields
        self.role_combobox = self._dropdown(form, "Role", self.role_name_to_id, 2, 0)
        
        # Configure column weights for responsiveness
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        # Pre-fill form if editing existing user
        if prefill:
            self.first_name_entry.insert(0, prefill[1])
            self.surname_entry.insert(0, prefill[2])
            self.email_entry.insert(0, prefill[3])
            role_name = prefill[4]
            if role_name in self.role_name_to_id:
                self.role_combobox.set(role_name)

    def _field(self, parent, label, row, col, show=None):
        """Create label and entry field pair"""
        tk.Label(
            parent, text=label, bg="white", font=("Arial", 10, "bold"),
        ).grid(row=row, column=col, padx=(0, 6), pady=3, sticky="w")

        entry = tk.Entry(parent, width=30, show=show)
        entry.grid(row=row, column=col + 1, padx=(0, 24), pady=3, sticky="we")
        return entry

    def _dropdown(self, parent, label, name_to_id, row, col):
        """Create label and combobox pair"""
        tk.Label(
            parent, text=label, bg="white", font=("Arial", 10, "bold"),
        ).grid(row=row, column=col, padx=(0, 6), pady=3, sticky="w")

        combo = ttk.Combobox(parent, state="readonly", width=28)
        combo["values"] = list(name_to_id.keys())
        combo.grid(row=row, column=col + 1, padx=(0, 24), pady=3, sticky="we")
        return combo

    # ========================================================================
    # DATA COLLECTION
    # ========================================================================

    def collect(self, require_password=False):
        """Collect and validate form data"""
        # Check if form is ready
        if self.first_name_entry is None:
            raise ValueError("Form is not ready yet. Please try again.")

        # Get form values
        first_name = self.first_name_entry.get().strip()
        surname    = self.surname_entry.get().strip()
        email      = self.email_entry.get().strip()
        password   = self.password_entry.get().strip()
        role_name  = self.role_combobox.get().strip()

        # Validate using centralized validation
        validate_user_form(first_name, surname, email, role_name, require_password, password)

        # Get role ID
        role_id = self.role_name_to_id.get(role_name)
        if role_id is None:
            raise ValueError("Please select a valid role.")

        return first_name, surname, email, password, role_id


# ============================================================================
# PAGE FACTORY
# ============================================================================

def create_page(parent, user_info=None):
    """Create and return user management page"""
    from main.user_page import UserManagementPage
    return UserManagementPage(parent, user_info=user_info).frame