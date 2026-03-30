# ============================================================================
# REQUEST MANAGEMENT MODULE
# Form to register and submit new maintenance requests
# ============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_button
from validations import validate_request_form


class RegisterRequestPanel:
    """Form to register and submit new maintenance requests"""

    def __init__(self, parent, user_info=None, on_submit=None, on_cancel=None):
        self.parent = parent
        self.user_info = user_info
        self.user_role = user_info[4] if user_info and len(user_info) > 4 else None
        self.user_id = user_info[0] if user_info else None
        self.on_submit = on_submit
        self.on_cancel = on_cancel

        self._tenant_context = None
        self._tenants = []
        self._tenant_names = []
        self._tenant_ids = []
        self._apartments = []
        self._apt_labels = []
        self._apt_ids = []

        self.tenant_cb = None
        self.apt_cb = None

        try:
            if self.user_role == "Tenant":
                from database.maintaince_service import get_valid_lease_apartments_for_user

                lease_rows = get_valid_lease_apartments_for_user(self.user_id) or []
                if lease_rows:
                    first_row = lease_rows[0]
                    self._tenant_context = {
                        "tenant_id": first_row[2],
                        "tenant_name": first_row[3] or "Tenant",
                    }
                    self._apartments = [(row[0], row[1]) for row in lease_rows]
            else:
                from database.maintaince_service import get_all_tenants
                self._tenants = get_all_tenants(user_info=user_info) or []
                self._tenant_names = [name for _, name in self._tenants]
                self._tenant_ids = [tenant_id for tenant_id, _ in self._tenants]
        except Exception as e:
            self._tenants = []
            self._tenant_names = []
            self._tenant_ids = []
            self._apartments = []
            messagebox.showerror("DB Error", f"Could not load form data:\n{e}")

        self._render()

    def _render(self):
        """Build the request registration form"""
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        tk.Label(
            wrapper,
            text="Register Maintenance Request",
            font=("Arial", 12, "bold"),
            bg="white",
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        if self.user_role == "Tenant":
            self._lbl(wrapper, "Tenant:", row=1)
            tk.Label(
                wrapper,
                text=(self._tenant_context or {}).get("tenant_name", "Unknown"),
                font=("Arial", 10),
                bg="white",
                anchor="w",
            ).grid(row=1, column=1, sticky="w", pady=4)

            self._lbl(wrapper, "Apartment:", row=2)
            self._set_apartment_options()
            self.apt_cb = ttk.Combobox(
                wrapper,
                values=self._apt_labels,
                state="readonly",
                width=42,
                font=("Arial", 10),
            )
            self.apt_cb.grid(row=2, column=1, sticky="w", pady=4)
            if self._apt_labels:
                self.apt_cb.current(0)
        else:
            self._lbl(wrapper, "Tenant:", row=1)
            self.tenant_cb = ttk.Combobox(
                wrapper,
                values=self._tenant_names,
                state="readonly",
                width=42,
                font=("Arial", 10),
            )
            self.tenant_cb.grid(row=1, column=1, sticky="w", pady=4)
            self.tenant_cb.bind("<<ComboboxSelected>>", self._on_tenant_selected)
            if self._tenant_names:
                self.tenant_cb.current(0)

            self._lbl(wrapper, "Apartment:", row=2)
            self.apt_cb = ttk.Combobox(
                wrapper,
                values=[],
                state="readonly",
                width=42,
                font=("Arial", 10),
            )
            self.apt_cb.grid(row=2, column=1, sticky="w", pady=4)
            self._refresh_apartments_for_selected_tenant()

        self._lbl(wrapper, "Issue:", row=3)
        self.issue_entry = tk.Entry(wrapper, font=("Arial", 10), width=32)
        self.issue_entry.grid(row=3, column=1, sticky="w", pady=4)

        self._lbl(wrapper, "Priority:", row=4)
        if self.user_role == "Tenant":
            tk.Label(
                wrapper,
                text="Set automatically by maintenance team",
                font=("Arial", 10),
                bg="white",
                anchor="w",
            ).grid(row=4, column=1, sticky="w", pady=4)
            self.priority_var = None
        else:
            self.priority_var = tk.StringVar(value="Medium")
            ttk.Combobox(
                wrapper,
                textvariable=self.priority_var,
                values=["High", "Medium", "Low"],
                state="readonly",
                width=15,
                font=("Arial", 10),
            ).grid(row=4, column=1, sticky="w", pady=4)

        wrapper.grid_columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        for text, bg, cmd, w in [
            ("Submit", "#28a745", self._submit, 140),
            ("Cancel", "#6c757d", self.on_cancel if self.on_cancel else lambda: None, 100),
        ]:
            create_button(
                btn_frame,
                text=text,
                width=w,
                height=45,
                bg=bg,
                fg="white",
                command=cmd,
                next_window_func=None,
                current_window=None,
            ).pack(side="left", padx=(0, 8))

    def _set_apartment_options(self):
        self._apt_ids = [apt_id for apt_id, _ in self._apartments]
        self._apt_labels = [label for _, label in self._apartments]

    def _on_tenant_selected(self, _event=None):
        self._refresh_apartments_for_selected_tenant()

    def _refresh_apartments_for_selected_tenant(self):
        if self.user_role == "Tenant":
            self._set_apartment_options()
            if self.apt_cb is not None:
                self.apt_cb["values"] = self._apt_labels
                if self._apt_labels:
                    self.apt_cb.current(0)
            return

        tenant_name = self.tenant_cb.get().strip() if self.tenant_cb else ""
        self._apartments = []
        self._apt_ids = []
        self._apt_labels = []

        if not tenant_name:
            if self.apt_cb is not None:
                self.apt_cb.set("")
                self.apt_cb["values"] = []
            return

        try:
            from database.maintaince_service import get_valid_lease_apartments_for_tenant

            tenant_id = self._tenant_ids[self._tenant_names.index(tenant_name)]
            self._apartments = get_valid_lease_apartments_for_tenant(tenant_id, user_info=self.user_info) or []
            self._set_apartment_options()
        except Exception as e:
            self._apartments = []
            self._apt_ids = []
            self._apt_labels = []
            messagebox.showerror("DB Error", f"Could not load apartments for tenant:\n{e}")

        if self.apt_cb is not None:
            self.apt_cb.set("")
            self.apt_cb["values"] = self._apt_labels
            if self._apt_labels:
                self.apt_cb.current(0)

    @staticmethod
    def _lbl(parent, text, row, anchor="w"):
        """Create a label for form field"""
        tk.Label(
            parent,
            text=text,
            font=("Arial", 10, "bold"),
            bg="white",
            anchor=anchor,
        ).grid(row=row, column=0, sticky=anchor, padx=(0, 10), pady=4)

    def _submit(self):
        """Handle form submission"""
        issue = self.issue_entry.get().strip()
        priority = self.priority_var.get().strip() if self.priority_var is not None else "Medium"

        if self.user_role == "Tenant":
            if not self._tenant_context:
                messagebox.showerror("Error", "No valid lease found for this tenant.")
                return

            tenant_name = self._tenant_context["tenant_name"]
            apt_label = self.apt_cb.get().strip() if self.apt_cb else ""
            tenant_id = self._tenant_context["tenant_id"]

            try:
                apartment_id = self._apt_ids[self._apt_labels.index(apt_label)]
            except ValueError:
                messagebox.showerror("Error", "Please select a valid apartment.")
                return

            try:
                validate_request_form(tenant_name, apt_label, issue, priority, require_priority=False)
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
                return
        else:
            tenant_name = self.tenant_cb.get().strip() if self.tenant_cb else ""
            apt_label = self.apt_cb.get().strip() if self.apt_cb else ""

            try:
                validate_request_form(tenant_name, apt_label, issue, priority)
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
                return

            try:
                tenant_id = self._tenant_ids[self._tenant_names.index(tenant_name)]
                apartment_id = self._apt_ids[self._apt_labels.index(apt_label)]
            except ValueError:
                messagebox.showerror("Error", "Selected tenant or apartment was not found — please try again.")
                return

        try:
            from database.maintaince_service import register_request
            new_id = register_request(
                apartment_id=apartment_id,
                tenant_id=tenant_id,
                issue=issue,
                priority=priority,
            )
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save request:\n{e}")
            return

        if new_id and self.on_submit:
            self.on_submit(new_id)
        elif not new_id:
            messagebox.showerror("Error", "Registration failed — no rows were inserted.")
