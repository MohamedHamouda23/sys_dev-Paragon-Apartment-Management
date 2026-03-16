import tkinter as tk
from tkinter import messagebox
from main.helpers import create_button, create_scrollable_treeview, show_placeholder
from database.maintaince_service import get_all_requests, viewFull, update_request_status, resolve_request

from modules.Lifecycle_Management import (
    StaffAssignmentPanel,
    MaintenanceDetailPanel,
)

class MaintenanceManagementPage:
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.selected_request_id = None
        self._panel = None
        self.request_status = {} 
        
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self._load_requests()

    def on_show(self):
        self.refresh_data()

    def refresh_data(self):
        self._load_requests()
        self.selected_request_id = None
        self._panel = None
        self.tree.selection_remove(self.tree.selection())
        self.assign_btn.config(bg="#dc3545", state="disabled")
        
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        show_placeholder(self.detail_wrap, "Select a request to view details")

    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        self.assign_btn = create_button(
            btns_inner_frame, text="Assign & Schedule", width=180, height=45,
            bg="#dc3545", fg="white", command=self._assign_and_schedule,
        )
        self.assign_btn.pack(side="left", padx=8)
        self.assign_btn.config(state="disabled")

        create_button(
            btns_inner_frame, text="Clear Form", width=110, height=45,
            bg="#3B86FF", fg="white", command=self._clear_form,
        ).pack(side="left", padx=8)

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        _table_wrap, self.tree = create_scrollable_treeview(
            parent=content_frame,
            columns=("id", "tenant", "issue", "date_submitted", "status"),
            headings=("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
            widths=(90, 160, 220, 140, 120),
            anchors=("center", "w", "w", "center", "center"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a request to view details")

    def _load_requests(self, reselect_id=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        self.request_status.clear()
        requests = get_all_requests(user_info=self.user_info) or []
        for row in requests:
            self.tree.insert("", "end", values=row)
            self.request_status[str(row[0])] = row[4]

        if reselect_id is not None:
            for item in self.tree.get_children():
                if str(self.tree.item(item, "values")[0]) == str(reselect_id):
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    break


    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected: return
            
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
        self._update_assign_button()
        
        full_data = viewFull(self.selected_request_id)
        self._panel = MaintenanceDetailPanel(
            parent=self.detail_wrap,
            full_data=full_data,
            on_approve=self._approve,
            on_deny=self._deny,
            on_resolve=self._on_resolved,
            # NEW CALLBACK:
            on_update_priority=self._refresh_after_priority_change 
        )

    def _refresh_after_priority_change(self, request_id):
        """Refreshes the data without losing the current selection"""
        self._load_requests(reselect_id=request_id)
        # Re-trigger row selection to refresh the detail panel itself
        self._on_row_select() 


        
    def _update_assign_button(self):
        if not self.selected_request_id:
            self.assign_btn.config(bg="#dc3545", state="disabled")
            return

        status = self.request_status.get(str(self.selected_request_id))
        if status == "Approved":
            self.assign_btn.config(bg="#28a745", state="normal")
        elif status == "In Progress":
            self.assign_btn.config(bg="#95a5a6", state="disabled")
        else:
            self.assign_btn.config(bg="#dc3545", state="disabled")

    def _assign_and_schedule(self):
        if not self.selected_request_id: return
        full_data = viewFull(self.selected_request_id)
        tenant_name = full_data[8] if full_data and len(full_data) > 8 else ""
        
        self._panel = StaffAssignmentPanel(
            parent=self.detail_wrap,
            request_id=self.selected_request_id,
            tenant_name=tenant_name,
            user_info=self.user_info,
            on_submit=self._on_staff_assigned_and_scheduled,
            on_cancel=self._on_row_select,
        )

    def _on_staff_assigned_and_scheduled(self, request_id, staff_name, comment):
        messagebox.showinfo("Success", f"Staff assigned to #{request_id}")
        self._load_requests(reselect_id=request_id)
        self._on_row_select()

    def _approve(self, request_id=None):
        # Use provided ID or fallback to selection
        target_id = request_id if request_id else self.selected_request_id
        if not target_id: return

        if update_request_status(target_id, "approve"):
            messagebox.showinfo("Approved", f"Request #{target_id} approved.")
            self._load_requests(reselect_id=target_id)
            self._on_row_select() # Refresh detail panel & button
        else:
            messagebox.showerror("Error", "Approval failed.")

    def _deny(self, request_id=None):
        target_id = request_id if request_id else self.selected_request_id
        if not target_id: return

        if update_request_status(target_id, "reject"):
            messagebox.showinfo("Denied", f"Request #{target_id} denied.")
            self._load_requests(reselect_id=target_id)
            self._on_row_select()
        else:
            messagebox.showerror("Error", "Denial failed.")

    def _on_resolved(self, notes, repair_time, repair_cost):
        if resolve_request(self.selected_request_id, notes, repair_time, repair_cost):
            messagebox.showinfo("Resolved", "Request marked as Resolved.")
            self._load_requests(reselect_id=self.selected_request_id)
            self._on_row_select()

    def _clear_form(self):
        self.refresh_data()