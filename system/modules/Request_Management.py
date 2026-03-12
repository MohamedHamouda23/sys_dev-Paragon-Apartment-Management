import re
import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_button


# ---------------------------------------------------------------------------
# RegisterRequestPanel
# FR4.5 — Form to register and submit a new maintenance request.
# Validates all fields before writing to the DB.
# Filters tenants and apartments based on user's city credentials.
# Callbacks: on_submit(new_request_id) | on_cancel()
# ---------------------------------------------------------------------------

class RegisterRequestPanel:

    def __init__(self, parent, user_info=None, on_submit=None, on_cancel=None):
        self.parent    = parent
        self.user_info = user_info
        self.on_submit = on_submit
        self.on_cancel = on_cancel

        # Load dropdown data filtered by user's city
        try:
            from database.maintaince_service import get_all_tenants, get_all_apartments
            self._tenants    = get_all_tenants(user_info=user_info)    or []
            self._apartments = get_all_apartments(user_info=user_info) or []
        except Exception as e:
            self._tenants    = []
            self._apartments = []
            messagebox.showerror("DB Error", f"Could not load form data:\n{e}")

        self._render()

    # ------------------------------------------------------------------ render

    def _render(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        tk.Label(
            wrapper, text="Register Maintenance Request",
            font=("Arial", 12, "bold"), bg="white", anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Tenant
        self._lbl(wrapper, "Tenant:", row=1)
        self._tenant_names = [n for _, n in self._tenants]
        self._tenant_ids   = [i for i, _ in self._tenants]

        self.tenant_cb = ttk.Combobox(
            wrapper, values=self._tenant_names,
            state="readonly", width=30, font=("Arial", 10),
        )
        self.tenant_cb.grid(row=1, column=1, sticky="w", pady=4)
        if self._tenant_names:
            self.tenant_cb.current(0)

        # Apartment
        self._lbl(wrapper, "Apartment:", row=2)
        self._apt_labels = [l for _, l in self._apartments]
        self._apt_ids    = [i for i, _ in self._apartments]

        self.apt_cb = ttk.Combobox(
            wrapper, values=self._apt_labels,
            state="readonly", width=30, font=("Arial", 10),
        )
        self.apt_cb.grid(row=2, column=1, sticky="w", pady=4)
        if self._apt_labels:
            self.apt_cb.current(0)

        # Issue (short title)
        self._lbl(wrapper, "Issue:", row=3)
        self.issue_var = tk.StringVar()
        tk.Entry(
            wrapper, textvariable=self.issue_var,
            font=("Arial", 10), width=32,
        ).grid(row=3, column=1, sticky="w", pady=4)

        # Description
        self._lbl(wrapper, "Description:", row=4, anchor="nw")
        self.desc_text = tk.Text(wrapper, width=32, height=4, font=("Arial", 10), wrap="word")
        self.desc_text.grid(row=4, column=1, sticky="ew", pady=4)

        # Priority
        self._lbl(wrapper, "Priority:", row=5)
        self.priority_var = tk.StringVar(value="Medium")
        ttk.Combobox(
            wrapper, textvariable=self.priority_var,
            values=["High", "Medium", "Low"],
            state="readonly", width=15, font=("Arial", 10),
        ).grid(row=5, column=1, sticky="w", pady=4)

        wrapper.grid_columnconfigure(1, weight=1)

        # Buttons
        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        for text, bg, cmd, w in [
            ("Submit", "#28a745", self._submit,                                       140),
            ("Cancel", "#6c757d", self.on_cancel if self.on_cancel else lambda: None, 100),
        ]:
            create_button(
                btn_frame, text=text, width=w, height=45,
                bg=bg, fg="white", command=cmd,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _lbl(parent, text, row, anchor="w"):
        tk.Label(
            parent, text=text, font=("Arial", 10, "bold"),
            bg="white", anchor=anchor,
        ).grid(row=row, column=0, sticky=anchor, padx=(0, 10), pady=4)

    # ------------------------------------------------------------------ submit

    def _submit(self):
        tenant_name = self.tenant_cb.get().strip()
        apt_label   = self.apt_cb.get().strip()
        issue       = self.issue_var.get().strip()
        description = self.desc_text.get("1.0", "end").strip()
        priority    = self.priority_var.get().strip()

        # Validate
        errors = []
        if not tenant_name:   errors.append("• Please select a tenant.")
        if not apt_label:     errors.append("• Please select an apartment.")
        if not issue:         errors.append("• Issue title is required.")
        if not description:   errors.append("• Description is required.")
        if not priority:      errors.append("• Please select a priority.")
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        # Resolve dropdown selections back to their DB IDs
        try:
            tenant_id    = self._tenant_ids[self._tenant_names.index(tenant_name)]
            apartment_id = self._apt_ids[self._apt_labels.index(apt_label)]
        except ValueError:
            messagebox.showerror("Error", "Selected value not found — please try again.")
            return

        # Insert into DB and return new request_id
        try:
            from database.maintaince_service import register_request
            new_id = register_request(
                apartment_id=apartment_id,
                tenant_id=tenant_id,
                issue=issue,
                description=description,
                priority=priority,
            )
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save request:\n{e}")
            return

        if new_id:
            if self.on_submit:
                self.on_submit(new_id)
        else:
            messagebox.showerror("Error", "Registration failed — no rows were inserted.")


# ---------------------------------------------------------------------------
# Page factory
# ---------------------------------------------------------------------------

def create_page(parent, user_info=None):
    from main.Request_page import RequestManagementPage
    return RequestManagementPage(parent, user_info=user_info).frame