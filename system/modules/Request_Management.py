# ============================================================================
# REQUEST MANAGEMENT MODULE
# Form to register and submit new maintenance requests
# ============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_button
from validations import validate_request_form
from database.tenant_portal_service import get_active_lease_for_user, get_tenant_profile


class RegisterRequestPanel:
    """Form to register and submit a new maintenance request"""

    def __init__(self, parent, user_info=None, on_submit=None, on_cancel=None):
        self.parent = parent
        self.user_info = user_info
        self.user_role = user_info[4] if user_info and len(user_info) > 4 else None
        self.user_id = user_info[0] if user_info else None
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self._tenant_context = None

        # Load tenants and apartments from database
        try:
            if self.user_role == "Tenant":
                lease = get_active_lease_for_user(self.user_id)
                profile = get_tenant_profile(self.user_id)
                if lease and profile:
                    self._tenant_context = {
                        "tenant_id": lease[1],
                        "apartment_id": lease[2],
                        "tenant_name": profile.get("name", "Tenant"),
                        "apartment_label": f"{profile.get('location', 'Assigned Apartment')} - {profile.get('apartment_type', 'N/A')}",
                    }
                self._tenants = []
                self._apartments = []
            else:
                from database.maintaince_service import get_all_tenants, get_all_apartments
                self._tenants = get_all_tenants(user_info=user_info) or []
                self._apartments = get_all_apartments(user_info=user_info) or []
        except Exception as e:
            self._tenants = []
            self._apartments = []
            messagebox.showerror("DB Error", f"Could not load form data:\n{e}")

        self._render()

    def _render(self):
        """Build the request registration form"""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        # Header
        tk.Label(
            wrapper, text="Register Maintenance Request",
            font=("Arial", 12, "bold"), bg="white", anchor="w",
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
            tk.Label(
                wrapper,
                text=(self._tenant_context or {}).get("apartment_label", "No active lease"),
                font=("Arial", 10),
                bg="white",
                anchor="w",
            ).grid(row=2, column=1, sticky="w", pady=4)
        else:
            # Tenant dropdown
            self._lbl(wrapper, "Tenant:", row=1)
            self._tenant_names = [n for _, n in self._tenants]
            self._tenant_ids = [i for i, _ in self._tenants]

            self.tenant_cb = ttk.Combobox(
                wrapper, values=self._tenant_names,
                state="readonly", width=30, font=("Arial", 10),
            )
            self.tenant_cb.grid(row=1, column=1, sticky="w", pady=4)
            if self._tenant_names:
                self.tenant_cb.current(0)

            # Apartment dropdown
            self._lbl(wrapper, "Apartment:", row=2)
            self._apt_labels = [l for _, l in self._apartments]
            self._apt_ids = [i for i, _ in self._apartments]

            self.apt_cb = ttk.Combobox(
                wrapper, values=self._apt_labels,
                state="readonly", width=30, font=("Arial", 10),
            )
            self.apt_cb.grid(row=2, column=1, sticky="w", pady=4)
            if self._apt_labels:
                self.apt_cb.current(0)

        # Issue title field
        self._lbl(wrapper, "Issue:", row=3)
        self.issue_entry = tk.Entry(
            wrapper, font=("Arial", 10), width=32,
        )
        self.issue_entry.grid(row=3, column=1, sticky="w", pady=4)

        # Priority dropdown
        self._lbl(wrapper, "Priority:", row=4)
        self.priority_var = tk.StringVar(value="Medium")
        ttk.Combobox(
            wrapper, textvariable=self.priority_var,
            values=["High", "Medium", "Low"],
            state="readonly", width=15, font=("Arial", 10),
        ).grid(row=4, column=1, sticky="w", pady=4)

        wrapper.grid_columnconfigure(1, weight=1)

        # Action buttons
        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        for text, bg, cmd, w in [
            ("Submit", "#28a745", self._submit, 140),
            ("Cancel", "#6c757d", self.on_cancel if self.on_cancel else lambda: None, 100),
        ]:
            create_button(
                btn_frame, text=text, width=w, height=45,
                bg=bg, fg="white", command=cmd,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

    @staticmethod
    def _lbl(parent, text, row, anchor="w"):
        """Create a label for form field"""
        tk.Label(
            parent, text=text, font=("Arial", 10, "bold"),
            bg="white", anchor=anchor,
        ).grid(row=row, column=0, sticky=anchor, padx=(0, 10), pady=4)

    def _submit(self):
        """Handle form submission"""
        issue = self.issue_entry.get().strip()
        priority = self.priority_var.get().strip()

        if self.user_role == "Tenant":
            if not self._tenant_context:
                messagebox.showerror("Error", "No active lease found for this tenant.")
                return
            tenant_name = self._tenant_context["tenant_name"]
            apt_label = self._tenant_context["apartment_label"]
            tenant_id = self._tenant_context["tenant_id"]
            apartment_id = self._tenant_context["apartment_id"]
            try:
                validate_request_form(tenant_name, apt_label, issue, priority)
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
                return
        else:
            tenant_name = self.tenant_cb.get().strip()
            apt_label = self.apt_cb.get().strip()

            # Validate form inputs
            try:
                validate_request_form(tenant_name, apt_label, issue, priority)
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
                return

            # Get IDs from selected values
            try:
                tenant_id = self._tenant_ids[self._tenant_names.index(tenant_name)]
                apartment_id = self._apt_ids[self._apt_labels.index(apt_label)]
            except ValueError:
                messagebox.showerror("Error", "Selected value not found — please try again.")
                return

        # Save to database
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

        # Handle success
        if new_id and self.on_submit:
            self.on_submit(new_id)
        elif not new_id:
            messagebox.showerror("Error", "Registration failed — no rows were inserted.")