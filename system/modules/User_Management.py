import tkinter as tk
from tkinter import ttk

# -- core imports for shared ui helpers
from main.helpers import (
    create_button, create_frame, clear_frame, styled_label,
    form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE, FONT_LABEL,
)


class UserFormStepper:

    def __init__(self, parent, role_name_to_id, city_name_to_id, prefill=None):
        self.parent          = parent
        self.role_name_to_id = role_name_to_id
        self.city_name_to_id = city_name_to_id
        self._render_form(prefill)

    # ------------------------------------------------------------------ render

    def _render_form(self, prefill=None):
        for widget in self.parent.winfo_children():
            widget.destroy()

        form = tk.Frame(self.parent, bg="white")
        form.pack(fill="x", padx=16, pady=(10, 10))

        # ── Text fields ───────────────────────────────────────────────────────
        self.first_name_entry = self._field(form, "First Name", 0, 0)
        self.surname_entry    = self._field(form, "Surname",    0, 2)
        self.email_entry      = self._field(form, "Email",      1, 0)
        self.password_entry   = self._field(form, "Password",   1, 2, show="*")

        # ── Dropdowns ─────────────────────────────────────────────────────────
        self.role_combobox = self._dropdown(form, "Role", self.role_name_to_id, 2, 0)
        self.city_combobox = self._dropdown(form, "City", self.city_name_to_id, 2, 2)

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        # ── Pre-populate if editing an existing user ──────────────────────────
        if prefill:
            # prefill: (id, first_name, surname, email, city, role)
            self.first_name_entry.insert(0, prefill[1])
            self.surname_entry.insert(0, prefill[2])
            self.email_entry.insert(0, prefill[3])
            city_name = prefill[4]
            role_name = prefill[5]
            if city_name in self.city_name_to_id:
                self.city_combobox.set(city_name)
            if role_name in self.role_name_to_id:
                self.role_combobox.set(role_name)

    def _field(self, parent, label, row, col, show=None):
        """Render a label + Entry pair and return the Entry widget."""
        tk.Label(
            parent, text=label, bg="white", font=("Arial", 10, "bold"),
        ).grid(row=row, column=col, padx=(0, 6), pady=3, sticky="w")

        entry = tk.Entry(parent, width=30, show=show)
        entry.grid(row=row, column=col + 1, padx=(0, 24), pady=3, sticky="we")
        return entry

    def _dropdown(self, parent, label, name_to_id, row, col):
        """Render a label + read-only Combobox pair and return the Combobox."""
        tk.Label(
            parent, text=label, bg="white", font=("Arial", 10, "bold"),
        ).grid(row=row, column=col, padx=(0, 6), pady=3, sticky="w")

        combo = ttk.Combobox(parent, state="readonly", width=28)
        combo["values"] = list(name_to_id.keys())
        combo.grid(row=row, column=col + 1, padx=(0, 24), pady=3, sticky="we")
        return combo

    # ------------------------------------------------------------------ collect

    def collect(self, require_password=False):
        first_name = self.first_name_entry.get().strip()
        surname    = self.surname_entry.get().strip()
        email      = self.email_entry.get().strip()
        password   = self.password_entry.get().strip()
        role_name  = self.role_combobox.get().strip()
        city_name  = self.city_combobox.get().strip()

        if not first_name or not surname or not email or not role_name:
            raise ValueError("First name, surname, email and role are required.")
        if require_password and not password:
            raise ValueError("Password is required when adding a user.")

        role_id = self.role_name_to_id.get(role_name)
        if role_id is None:
            raise ValueError("Please select a valid role.")

        city_id = self.city_name_to_id.get(city_name)
        return first_name, surname, email, password, role_id, city_id


def create_page(parent, user_info=None):
    # Local import to avoid circular import; fixed case
    from main.user_page import UserManagementPage
    return UserManagementPage(parent, user_info=user_info).frame