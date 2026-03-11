import tkinter as tk
from tkinter import ttk, messagebox

# ---------------------------------------------------------------------------
# Placeholder frame — replace with real implementation as features are built
# ---------------------------------------------------------------------------

class LoggingAndRecordsPage:


    def __init__(self, parent, user_info=None):
        self.parent    = parent
        self.user_info = user_info
        self.frame     = tk.Frame(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(
            self.frame,
            text="Logging & Records",
            font=("Arial", 14, "bold"),
            bg="white",
        ).pack(anchor="w", padx=16, pady=(12, 6))

        # FR5.2 – request list
        # TODO: populate from database.maintaince_service.get_all_requests()
        #       when that query is available.
        self._build_request_table()

        # FR5.3 – status update
        # TODO: add status-dropdown + save button bound to update_request_status()

        # FR4.5 – registration form
        # TODO: add "New Request" button that opens a registration form

        # FR4.6 – log / audit trail
        # TODO: add a log viewer panel below the table

        # FR5.4 – notes editor
        # TODO: integrate notes text field into the detail/edit panel

        # FR5.5 – cost & time log
        # NOTE: repair_time + repair_cost are already collected in
        #       Request_Lifecycle.MaintenanceDetailPanel._open_resolve_form()
        #       and passed back via the on_resolve callback. Store / display
        #       those values here once the DB write is wired up.

    def _build_request_table(self):
        columns = (
            "Request ID", "Issue", "Priority", "Status",
            "Date Submitted", "Tenant", "Staff",
        )

        frame = tk.Frame(self.frame, bg="white")
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        tree = ttk.Treeview(frame, columns=columns, show="headings", height=16)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.request_tree = tree
        # TODO: call _load_requests() once DB service is available


# ---------------------------------------------------------------------------
# Page factory
# ---------------------------------------------------------------------------
def create_page(parent, user_info=None):
    return LoggingAndRecordsPage(parent, user_info=user_info).frame