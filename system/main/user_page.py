# ============================================================================
# USER MANAGEMENT PAGE
# Main page for managing users with table and form
# ============================================================================

import tkinter as tk
from tkinter import messagebox

from main.helpers import create_button, create_scrollable_treeview, show_placeholder
from database.user_service import (
    get_all_users,
    get_all_roles,
    create_user,
    update_user,
    delete_user,
)
from modules.User_Management import UserFormStepper


class UserManagementPage:
    """User management page with CRUD operations"""

    def __init__(self, parent, user_info=None):
        # Store parent and user info
        self.parent    = parent
        self.user_info = user_info
        self.selected_user_id = None
        self._stepper  = None

        # Extract logged-in user role and city scope
        self.logged_in_role      = None
        self.admin_scope_city_id = None
        if user_info and len(user_info) >= 6:
            self.logged_in_role = user_info[4]
            if self.logged_in_role == "Administrators":
                self.admin_scope_city_id = user_info[5]

        # Initialize lookup dictionaries
        self.role_name_to_id = {}

        # Create main frame
        self.frame = tk.Frame(parent, bg="#c9e4c4")

        # Build UI components
        self._build_layout()
        self._load_lookups()
        self._load_users()

    # ========================================================================
    # BUILD LAYOUT
    # ========================================================================

    def _build_layout(self):
        """Create the page layout with buttons, table, and detail panel"""
        # Top button bar
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        # Create action buttons
        for text, cmd, w in [
            ("Add User",    self._add_user,    120),
            ("Update User", self._update_user, 130),
            ("Delete User", self._delete_user, 130),
            ("Clear Form",  self._clear_form,  120),
        ]:
            create_button(
                btns_inner_frame, text=text, width=w, height=45,
                bg="#3B86FF", fg="white", command=cmd,
            ).pack(side="left", padx=8)

        # Content area with table and detail panel
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        # Create scrollable table
        _table_wrap, self.tree = create_scrollable_treeview(
            parent   = content_frame,
            columns  = ("id", "first_name", "surname", "email", "role"),
            headings = ("ID", "First Name", "Surname", "Email", "Role"),
            widths   = (55, 160, 160, 240, 190),
            anchors  = ("center", "w", "w", "w", "w"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Detail panel (form area)
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a user to view or edit details")

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def _load_lookups(self):
        """Load roles from database"""
        # Load roles
        roles = get_all_roles()
        self.role_name_to_id = {name: role_id for role_id, name in roles}

    def _load_users(self):
        """Load users into table from database"""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        # Insert user rows (scoped by admin city if applicable)
        for user in get_all_users(scope_city_id=self.admin_scope_city_id):
            self.tree.insert("", "end", values=user)

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    def _on_row_select(self, _event=None):
        """Handle row selection in table"""
        selected = self.tree.selection()
        if not selected:
            return

        # Get selected user data
        user_values = self.tree.item(selected[0], "values")
        self.selected_user_id = int(user_values[0])

        # Show form with selected user data
        self._stepper = UserFormStepper(
            parent          = self.detail_wrap,
            role_name_to_id = self.role_name_to_id,
            prefill         = user_values,
        )

    # ========================================================================
    # CRUD ACTIONS
    # ========================================================================

    def _add_user(self):
        """Add new user or save current form"""
        if self._stepper is None:
            # First click: show blank form
            self._stepper = UserFormStepper(
                parent          = self.detail_wrap,
                role_name_to_id = self.role_name_to_id,
                prefill         = None,
            )
            self.selected_user_id = None
            return

        # Second click: save user
        try:
            first_name, surname, email, password, role_id = \
                self._stepper.collect(require_password=True)
            city_id = self.admin_scope_city_id
            create_user(
                first_name, surname, email, password, role_id, city_id,
                scope_city_id=self.admin_scope_city_id,
            )
            self._load_users()
            self._clear_form()
            messagebox.showinfo("Success", "User added successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def _update_user(self):
        """Update selected user"""
        if self.selected_user_id is None:
            messagebox.showerror("Selection Error", "Please select a user from the table first.")
            return
        try:
            first_name, surname, email, password, role_id = \
                self._stepper.collect(require_password=False)
            city_id = self.admin_scope_city_id
            update_user(
                self.selected_user_id, first_name, surname, email, role_id, city_id,
                password_hash=password if password else None,
                scope_city_id=self.admin_scope_city_id,
            )
            self._load_users()
            messagebox.showinfo("Success", "User updated successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def _delete_user(self):
        """Delete selected user"""
        if self.selected_user_id is None:
            messagebox.showerror("Selection Error", "Please select a user from the table first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?"):
            return
        try:
            current_user_id = self.user_info[0] if self.user_info else None
            delete_user(
                self.selected_user_id,
                scope_city_id=self.admin_scope_city_id,
                acting_user_id=current_user_id,
                acting_role=self.logged_in_role,
            )
            self._load_users()
            self._clear_form()
            messagebox.showinfo("Success", "User deleted successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def _clear_form(self):
        """Clear form and deselect table row"""
        self.selected_user_id = None
        self._stepper = None
        self.tree.selection_remove(self.tree.selection())
        # Defer placeholder restore to avoid macOS crash
        self.detail_wrap.after(0, lambda: show_placeholder(
            self.detail_wrap, "Select a user to view or edit details"
        ))