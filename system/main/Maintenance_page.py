import tkinter as tk
from tkinter import messagebox

from database.maintaince_service import get_all_requests, viewFull, update_request_status
from main.helpers import create_button, create_scrollable_treeview, show_placeholder, clear_frame
from modules.Maintenance_Management import MaintenanceDetailPanel, AssignStaffPanel


class MaintenanceManagementPage:

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.selected_request_id = None
        self._panel = None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self._load_requests()


    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        for text, cmd, w in [
            ("Assign Staff", self._assign_staff, 140),
            ("View All",     self._view_all,     110),
        ]:
            create_button(
                btns_inner_frame, text=text, width=w, height=45,
                bg="#3B86FF", fg="white", command=cmd,
            ).pack(side="left", padx=8)

        # ── Content area ──────────────────────────────────────────────────────
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        # ── Treeview ──────────────────────────────────────────────────────────
        _table_wrap, self.tree = create_scrollable_treeview(
            parent   = content_frame,
            columns  = ("id", "tenant", "issue", "date_submitted", "status"),
            headings = ("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
            widths   = (90, 160, 220, 140, 120),
            anchors  = ("center", "w", "w", "center", "center"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # ── Detail panel ──────────────────────────────────────────────────────
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))

        show_placeholder(self.detail_wrap, "Select a request to view details")

    # ------------------------------------------------------------------ data

    def _load_requests(self):
        clear_frame(self.tree)  # clears only tree rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in (get_all_requests() or []):
            self.tree.insert("", "end", values=row)

    # ------------------------------------------------------------------ events

    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]

        self._panel = MaintenanceDetailPanel(
            parent     = self.detail_wrap,
            full_data  = viewFull(self.selected_request_id),
            on_approve = self._approve,
            on_deny    = self._deny,
        )

    # ------------------------------------------------------------------ actions

    def _require_selection(self):
        if self.selected_request_id is None:
            messagebox.showerror("Selection Error", "Please select a request from the table first.")
            return False
        return True

    def _assign_staff(self):
        if not self._require_selection():
            return
        self._panel = AssignStaffPanel(
            parent     = self.detail_wrap,
            request_id = self.selected_request_id,
            on_submit  = self._on_staff_assigned,
            on_cancel  = self._on_row_select,
        )

    def _on_staff_assigned(self, request_id, staff_name):
        messagebox.showinfo(
            "Success",
            f"'{staff_name}' has been assigned to request #{request_id}.\n"
            f"Status updated to 'In Progress'."
        )
        self._load_requests()
        self._on_row_select()

    def _update_status(self, action, success_msg, error_msg="Request not found."):
        """Shared logic for approve/deny — avoids duplicating the same pattern."""
        if not self._require_selection():
            return
        if update_request_status(self.selected_request_id, action):
            messagebox.showinfo("Success", success_msg)
            self._on_row_select()
        else:
            messagebox.showerror("Error", error_msg)

    def _approve(self):
        self._update_status("approve", "Request approved.")

    def _deny(self):
        self._update_status("reject", "Request denied.")

    def _view_all(self):
        self.selected_request_id = None
        self._panel = None
        self.tree.selection_remove(self.tree.selection())
        show_placeholder(self.detail_wrap, "Select a request to view details")
        self._load_requests()