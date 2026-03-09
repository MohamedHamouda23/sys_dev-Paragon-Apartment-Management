import tkinter as tk


class MaintenanceDetailPanel:
    """
    Renders the read-only detail grid for a single maintenance request.
    Analogous to UserFormStepper in modules/User_Management.py.
    """

    LABELS = (
        "Request ID", "Issue", "Description", "Priority", "Date Submitted",
        "Resolved Date", "Status", "Notes", "Tenant", "Apt Type",
        "Postcode", "Staff", "Assigned Date", "Is Current",
    )

    def __init__(self, parent, full_data):
        """
        parent    – the container frame (detail_wrap)
        full_data – tuple/list returned by viewFull(request_id)
        """
        self.parent = parent
        self._render(full_data)

    # ------------------------------------------------------------------ render

    def _render(self, full_data):
        for widget in self.parent.winfo_children():
            widget.destroy()

        grid_frame = tk.Frame(self.parent, bg="white")
        grid_frame.pack(fill="x", padx=16, pady=(10, 10))

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


def create_page(parent, user_info=None):
    from main.Maintenance_page import MaintenanceManagementPage
    return MaintenanceManagementPage(parent, user_info=user_info).frame