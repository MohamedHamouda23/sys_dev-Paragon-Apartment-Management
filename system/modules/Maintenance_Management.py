import tkinter as tk
from main.helpers import create_button


class MaintenanceDetailPanel:
    LABELS = (
        "Request ID", "Issue", "Description", "Priority", "Date Submitted",
        "Resolved Date", "Status", "Notes", "Tenant", "Apt Type",
        "Postcode", "Staff", "Assigned Date", "Is Current",
    )

    def __init__(self, parent, full_data, on_approve=None, on_deny=None):
        self.parent = parent
        self.on_approve = on_approve
        self.on_deny = on_deny
        self._render(full_data)

    def _render(self, full_data):
        for widget in self.parent.winfo_children():
            widget.destroy()

        # ── Detail grid ───────────────────────────────────────────────────────
        grid_frame = tk.Frame(self.parent, bg="white")
        grid_frame.pack(fill="x", padx=16, pady=(10, 6))

        for i, (lbl, val) in enumerate(zip(self.LABELS, full_data)):
            row, col = divmod(i, 2)
            col_offset = col * 2
            tk.Label(
                grid_frame,
                text=f"{lbl}:",
                font=("Arial", 10, "bold"),
                bg="white",
                anchor="w",
            ).grid(row=row, column=col_offset, sticky="w", padx=(10, 4), pady=3)
            tk.Label(
                grid_frame,
                text=val if val is not None else "—",
                bg="white",
                anchor="w",
            ).grid(row=row, column=col_offset + 1, sticky="w", padx=(0, 24), pady=3)

        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_columnconfigure(3, weight=1)

        # ── Approve / Deny buttons ─────────────────────────────────────────────
        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        create_button(
            btn_frame,
            text="Approve",
            width=140,
            height=45,
            bg="#28a745",       # ← green
            fg="white",
            command=self.on_approve if self.on_approve else lambda: None,
            next_window_func=None,
            current_window=None,
        ).pack(side="left", padx=(0, 8))

        create_button(
            btn_frame,
            text="Deny",
            width=140,
            height=45,
            bg="#dc3545",       # ← red
            fg="white",
            command=self.on_deny if self.on_deny else lambda: None,
            next_window_func=None,
            current_window=None,
        ).pack(side="left")


def create_page(parent, user_info=None):
    from main.Maintenance_page import MaintenanceManagementPage
    return MaintenanceManagementPage(parent, user_info=user_info).frame