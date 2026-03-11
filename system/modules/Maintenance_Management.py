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

        # ── Status (index 6) and Staff name (index 11) ────────────────────────
        status     = (full_data[6]  or "").strip() if len(full_data) > 6  else ""
        staff_name = (full_data[11] or "").strip() if len(full_data) > 11 else ""
        has_staff  = bool(staff_name)

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        if status == "Open":
            # Approve → goes to In Progress, Deny → goes to Denied
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
            # Staff assigned → can mark as resolved
            create_button(
                btn_frame, text="Mark as Resolved", width=180, height=45,
                bg="#17a2b8", fg="white",
                command=self.on_resolve if self.on_resolve else lambda: None,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

        # "In Progress" (no staff yet), "Resolved", "Denied" → no buttons


# ─────────────────────────────────────────────────────────────────────────────
# Page factory
# ─────────────────────────────────────────────────────────────────────────────
def create_page(parent, user_info=None):
    from main.Maintenance_page import MaintenanceManagementPage
    return MaintenanceManagementPage(parent, user_info=user_info).frame