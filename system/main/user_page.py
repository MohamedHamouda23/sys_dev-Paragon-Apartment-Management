import tkinter as tk
from tkinter import messagebox

from main.helpers import create_button, create_scrollable_treeview, show_placeholder
from database.user_service import (
    get_all_users,
    get_all_roles,
    get_all_locations,
    create_user,
    update_user,
    delete_user,
)
from modules.User_Management import UserFormStepper


class UserManagementPage:

    def __init__(self, parent, user_info=None):
        self.parent    = parent
        self.user_info = user_info
        self.selected_user_id = None
        self._stepper  = None

        self.logged_in_role      = None
        self.admin_scope_city_id = None
        if user_info and len(user_info) >= 6:
            self.logged_in_role = user_info[4]
            if self.logged_in_role == "Administrators":
                self.admin_scope_city_id = user_info[5]

        self.role_name_to_id = {}
        self.city_name_to_id = {}

        self.frame = tk.Frame(parent, bg="#c9e4c4")

        self._build_layout()
        self._load_lookups()
        self._load_users()

    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

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

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        _table_wrap, self.tree = create_scrollable_treeview(
            parent   = content_frame,
            columns  = ("id", "first_name", "surname", "email", "city", "role"),
            headings = ("ID", "First Name", "Surname", "Email", "City", "Role"),
            widths   = (55, 140, 140, 210, 140, 170),
            anchors  = ("center", "w", "w", "w", "w", "w"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # ── Detail panel (always visible) ─────────────────────────────────────
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))

        show_placeholder(self.detail_wrap, "Select a user to view or edit details")

    def _load_lookups(self):
        roles = get_all_roles()
        self.role_name_to_id = {name: role_id for role_id, name in roles}

        cities = get_all_locations(scope_city_id=self.admin_scope_city_id)
        self.city_name_to_id = {name: city_id for city_id, name in cities}

    def _load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for user in get_all_users(scope_city_id=self.admin_scope_city_id):
            self.tree.insert("", "end", values=user)

    # ------------------------------------------------------------------ events

    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        user_values = self.tree.item(selected[0], "values")
        self.selected_user_id = int(user_values[0])

        self._stepper = UserFormStepper(
            parent          = self.detail_wrap,
            role_name_to_id = self.role_name_to_id,
            city_name_to_id = self.city_name_to_id,
            prefill         = user_values,
        )

    # ------------------------------------------------------------------ actions

    def _add_user(self):
        if self._stepper is None:
            # First click: open blank form
            self._stepper = UserFormStepper(
                parent          = self.detail_wrap,
                role_name_to_id = self.role_name_to_id,
                city_name_to_id = self.city_name_to_id,
                prefill         = None,
            )
            self.selected_user_id = None
            return

        # Second click (form already open): save
        try:
            first_name, surname, email, password, role_id, city_id = \
                self._stepper.collect(require_password=True)
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
        if self.selected_user_id is None:
            messagebox.showerror("Selection Error", "Please select a user from the table first.")
            return
        try:
            first_name, surname, email, password, role_id, city_id = \
                self._stepper.collect(require_password=False)
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
        self.selected_user_id = None
        self._stepper = None
        self.tree.selection_remove(self.tree.selection())
        # Defer placeholder restore to avoid autorelease pool crash on macOS
        self.detail_wrap.after(0, lambda: show_placeholder(
            self.detail_wrap, "Select a user to view or edit details"
        ))