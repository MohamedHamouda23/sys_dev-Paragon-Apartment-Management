
import tkinter as tk
from tkinter import messagebox
from main.helpers import create_button


class AssignStaffPanel:
    def __init__(self, parent, request_id, on_submit=None, on_cancel=None):
        self.parent     = parent
        self.request_id = request_id
        self.on_submit  = on_submit
        self.on_cancel  = on_cancel

        try:
            from database.maintaince_service import get_all_staff
            self._staff_list = get_all_staff() or []
        except Exception as e:
            self._staff_list = []
            messagebox.showerror("DB Error", f"Could not load staff list:\n{e}")

        self._render()

    def _render(self):
        from tkinter import ttk

        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        tk.Label(
            wrapper,
            text=f"Assign Staff  —  Request #{self.request_id}",
            font=("Arial", 12, "bold"),
            bg="white", anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(
            wrapper, text="Staff Member:", font=("Arial", 10, "bold"),
            bg="white", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)

        self._staff_names = [name for _, name in self._staff_list]
        self._staff_ids   = [eid  for eid, _ in self._staff_list]

        self.staff_dropdown = ttk.Combobox(
            wrapper,
            values=self._staff_names,
            state="readonly",
            width=28,
            font=("Arial", 10),
        )
        self.staff_dropdown.grid(row=1, column=1, sticky="w", pady=4)
        if self._staff_names:
            self.staff_dropdown.current(0)

        tk.Label(
            wrapper, text="Notes:", font=("Arial", 10, "bold"),
            bg="white", anchor="nw",
        ).grid(row=2, column=0, sticky="nw", padx=(0, 10), pady=4)

        self.notes_text = tk.Text(
            wrapper, width=40, height=3, font=("Arial", 10), wrap="word",
        )
        self.notes_text.grid(row=2, column=1, sticky="w", pady=4)
        wrapper.grid_columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        for text, bg, cmd, w in [
            ("Assign", "#3B86FF", self._submit,                                       140),
            ("Cancel", "#6c757d", self.on_cancel if self.on_cancel else lambda: None, 100),
        ]:
            create_button(
                btn_frame, text=text, width=w, height=45,
                bg=bg, fg="white", command=cmd,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

    def _submit(self):
        staff_name = self.staff_dropdown.get().strip()
        notes      = self.notes_text.get("1.0", "end").strip()

        if not staff_name:
            messagebox.showerror("Validation Error", "Please select a staff member.")
            return

        try:
            employee_id = self._staff_ids[self._staff_names.index(staff_name)]
        except ValueError:
            messagebox.showerror("Error", "Selected staff member not found.")
            return

        try:
            from database.maintaince_service import assign_staff
            result = assign_staff(self.request_id, employee_id, notes or None)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not assign staff:\n{e}")
            return

        if result:
            if self.on_submit:
                self.on_submit(self.request_id, staff_name)
        else:
            messagebox.showerror("Error", "Assignment failed — no rows were updated.")




class MaintenanceDetailPanel:
    LABELS = (
        "Request ID", "Issue", "Description", "Priority", "Date Submitted",
        "Resolved Date", "Status", "Notes", "Tenant", "Apt Type",
        "Postcode", "Staff", "Assigned Date", "Is Current",
    )

    def __init__(self, parent, full_data, on_approve=None, on_deny=None, on_resolve=None):
        self.parent     = parent
        self.on_approve = on_approve
        self.on_deny    = on_deny
        self.on_resolve = on_resolve
        self._render(full_data)

    # ── detail grid ────────────────────────────────────────────────────────
    def _render(self, full_data):
        for widget in self.parent.winfo_children():
            widget.destroy()

        grid_frame = tk.Frame(self.parent, bg="white")
        grid_frame.pack(fill="x", padx=16, pady=(10, 6))

        for i, (lbl, val) in enumerate(zip(self.LABELS, full_data)):
            row, col = divmod(i, 2)
            tk.Label(
                grid_frame, text=f"{lbl}:", font=("Arial", 10, "bold"),
                bg="white", anchor="w"
            ).grid(row=row, column=col * 2, sticky="w", padx=(10, 4), pady=3)
            tk.Label(
                grid_frame, text=val or "—", bg="white", anchor="w"
            ).grid(row=row, column=col * 2 + 1, sticky="w", padx=(0, 24), pady=3)

        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_columnconfigure(3, weight=1)

        status     = (full_data[6]  or "").strip() if len(full_data) > 6  else ""
        staff_name = (full_data[11] or "").strip() if len(full_data) > 11 else ""
        has_staff  = bool(staff_name)

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        # FR1.7 – approve / deny open requests
        if status == "Open":
            for text, bg, cmd in [
                ("Approve", "#28a745", self.on_approve),
                ("Deny",    "#dc3545", self.on_deny),
            ]:
                create_button(
                    btn_frame, text=text, width=140, height=45,
                    bg=bg, fg="white",
                    command=cmd if cmd else lambda: None,
                    next_window_func=None, current_window=None,
                ).pack(side="left", padx=(0, 8))

        # FR2.6 – mark as resolved once staff are assigned
        elif status == "In Progress" and has_staff:
            create_button(
                btn_frame, text="Mark as Resolved", width=180, height=45,
                bg="#17a2b8", fg="white",
                command=self._open_resolve_form,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

        # "In Progress" (no staff), "Resolved", "Denied" → no action buttons

    # ── resolution form (FR2.6 + FR2.7) ────────────────────────────────────
    def _open_resolve_form(self):
        """Replace detail panel with the resolution form."""
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        tk.Label(
            wrapper, text="Resolution Details",
            font=("Arial", 13, "bold"), bg="white", anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        # Resolution description
        tk.Label(
            wrapper, text="Resolution Description:", font=("Arial", 10, "bold"),
            bg="white", anchor="nw"
        ).grid(row=1, column=0, sticky="nw", padx=(0, 10), pady=4)

        self.resolve_desc = tk.Text(wrapper, width=40, height=3, font=("Arial", 10), wrap="word")
        self.resolve_desc.grid(row=1, column=1, sticky="w", pady=4)

        tk.Label(
            wrapper, text="Repair Time (hours):", font=("Arial", 10, "bold"),
            bg="white", anchor="w"
        ).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)

        self.repair_time_var = tk.StringVar()
        tk.Entry(
            wrapper, textvariable=self.repair_time_var,
            font=("Arial", 10), width=15
        ).grid(row=2, column=1, sticky="w", pady=4)

        tk.Label(
            wrapper, text="Repair Cost (£):", font=("Arial", 10, "bold"),
            bg="white", anchor="w"
        ).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=4)

        self.repair_cost_var = tk.StringVar()
        tk.Entry(
            wrapper, textvariable=self.repair_cost_var,
            font=("Arial", 10), width=15
        ).grid(row=3, column=1, sticky="w", pady=4)

        wrapper.grid_columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        for text, bg, cmd, w in [
            ("Submit", "#28a745", self._submit_resolve, 140),
            ("Cancel", "#6c757d", self._cancel_resolve, 100),
        ]:
            create_button(
                btn_frame, text=text, width=w, height=45,
                bg=bg, fg="white", command=cmd,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

    def _submit_resolve(self):
        description     = self.resolve_desc.get("1.0", "end").strip()
        repair_time_str = self.repair_time_var.get().strip()
        repair_cost_str = self.repair_cost_var.get().strip()

        if not description:
            messagebox.showerror("Validation Error", "Please enter a resolution description.")
            return

        repair_time = None
        if repair_time_str:
            try:
                repair_time = int(repair_time_str)
                if repair_time < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validation Error", "Repair time must be a positive whole number.")
                return

        repair_cost = None
        if repair_cost_str:
            try:
                repair_cost = float(repair_cost_str)
                if repair_cost < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validation Error", "Repair cost must be a positive number.")
                return

        if self.on_resolve:
            self.on_resolve(description, repair_time, repair_cost)

    def _cancel_resolve(self):
        """Return to the placeholder — parent page re-renders on next row select."""
        for widget in self.parent.winfo_children():
            widget.destroy()
        tk.Label(
            self.parent, text="Select a request to view details",
            bg="white", fg="grey", font=("Arial", 10, "italic")
        ).pack(expand=True, pady=20)



def create_page(parent, user_info=None):

    from main.Maintenance_page import MaintenanceManagementPage
    return MaintenanceManagementPage(parent, user_info=user_info).frame