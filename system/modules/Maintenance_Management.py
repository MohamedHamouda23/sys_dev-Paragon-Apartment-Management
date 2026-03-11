import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_button
from modules.Assign_Staff import AssignStaffPanel


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

        elif status == "In Progress" and has_staff:
            create_button(
                btn_frame, text="Mark as Resolved", width=180, height=45,
                bg="#17a2b8", fg="white",
                command=self._open_resolve_form,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

        # "In Progress" (no staff), "Resolved", "Denied" → no buttons

    def _open_resolve_form(self):
        """Replace detail panel with resolution form."""
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

        # Repair time
        tk.Label(
            wrapper, text="Repair Time (hours):", font=("Arial", 10, "bold"),
            bg="white", anchor="w"
        ).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)

        self.repair_time_var = tk.StringVar()
        tk.Entry(
            wrapper, textvariable=self.repair_time_var,
            font=("Arial", 10), width=15
        ).grid(row=2, column=1, sticky="w", pady=4)

        # Repair cost
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
            ("Submit",  "#28a745", self._submit_resolve, 140),
            ("Cancel",  "#6c757d", self._cancel_resolve, 100),
        ]:
            create_button(
                btn_frame, text=text, width=w, height=45,
                bg=bg, fg="white", command=cmd,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

    def _submit_resolve(self):
        description = self.resolve_desc.get("1.0", "end").strip()
        repair_time_str = self.repair_time_var.get().strip()
        repair_cost_str = self.repair_cost_var.get().strip()

        if not description:
            messagebox.showerror("Validation Error", "Please enter a resolution description.")
            return

        # Validate repair_time
        repair_time = None
        if repair_time_str:
            try:
                repair_time = int(repair_time_str)
                if repair_time < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validation Error", "Repair time must be a positive whole number.")
                return

        # Validate repair_cost
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
        """Go back — parent page will re-render the detail panel."""
        if self.on_resolve:
            # Signal cancel by passing None values — page handles re-render
            pass
        # Re-trigger row select to restore normal detail view
        for widget in self.parent.winfo_children():
            widget.destroy()
        tk.Label(
            self.parent, text="Select a request to view details",
            bg="white", fg="grey", font=("Arial", 10, "italic")
        ).pack(expand=True, pady=20)


# ─────────────────────────────────────────────────────────────────────────────
# Page factory
# ─────────────────────────────────────────────────────────────────────────────
def create_page(parent, user_info=None):
    from main.Maintenance_page import MaintenanceManagementPage
    return MaintenanceManagementPage(parent, user_info=user_info).frame