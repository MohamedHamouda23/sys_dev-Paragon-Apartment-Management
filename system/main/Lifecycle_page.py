# ============================================================================
# LIFECYCLE MANAGEMENT PAGE
# Main page for managing request lifecycle (approve/deny/assign/resolve)
# ============================================================================

import tkinter as tk
from tkinter import messagebox
from main.helpers import create_button, create_scrollable_treeview, show_placeholder
from database.maintaince_service import get_all_requests, viewFull, update_request_status, resolve_request

from modules.Lifecycle_Management import (
    StaffAssignmentPanel,
    MaintenanceDetailPanel,
)


class MaintenanceManagementPage:
    """Lifecycle management page with approve/deny/assign/resolve workflows"""

    def __init__(self, parent, user_info=None):
        # Store parent and user info
        self.parent = parent
        self.user_info = user_info
        self.selected_request_id = None
        self._panel = None
        self.request_status = {}  # Track request status for button state
        
        # Create main frame
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        
        # Build UI components
        self._build_layout()
        self._load_requests()

    # ========================================================================
    # REFRESH METHOD
    # ========================================================================
    def on_show(self):
        """Called when page becomes visible - refresh data"""
        self.refresh_data()

    def refresh_data(self):
        """Refresh the request list from database"""
        # Reload requests from database
        self._load_requests()
        
        # Clear selection and detail panel
        self.selected_request_id = None
        self._panel = None
        self.tree.selection_remove(self.tree.selection())
        self.assign_btn.config(bg="#dc3545", state="disabled")
        
        # Show placeholder in detail panel
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        show_placeholder(self.detail_wrap, "Select a request to view details")
        
        print("Lifecycle Management page refreshed")

    # ========================================================================
    # BUILD LAYOUT
    # ========================================================================

    def _build_layout(self):
        """Create the page layout with buttons, table, and detail panel"""
        # Top button bar
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        # Assign & Schedule button (color changes based on status)
        self.assign_btn = create_button(
            btns_inner_frame, text="Assign & Schedule", width=180, height=45,
            bg="#dc3545", fg="white", command=self._assign_and_schedule,
        )
        self.assign_btn.pack(side="left", padx=8)
        self.assign_btn.config(state="disabled")

        # Clear Form button
        create_button(
            btns_inner_frame, text="Clear Form", width=110, height=45,
            bg="#3B86FF", fg="white", command=self._clear_form,
        ).pack(side="left", padx=8)

        # Content area with table and detail panel
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        # Create scrollable table
        _table_wrap, self.tree = create_scrollable_treeview(
            parent=content_frame,
            columns=("id", "tenant", "issue", "date_submitted", "status"),
            headings=("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
            widths=(90, 160, 220, 140, 120),
            anchors=("center", "w", "w", "center", "center"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Detail panel (shows full request info)
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a request to view details")

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def _load_requests(self, reselect_id=None):
        """Load requests into table from database (filtered by user's city)"""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Insert request rows and store statuses
        requests = get_all_requests(user_info=self.user_info) or []
        for row in requests:
            self.tree.insert("", "end", values=row)
            if len(row) >= 5:
                self.request_status[row[0]] = row[4]

        # Optionally reselect a specific request
        if reselect_id is not None:
            for item in self.tree.get_children():
                if str(self.tree.item(item, "values")[0]) == str(reselect_id):
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    self.tree.see(item)
                    break

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    def _on_row_select(self, _event=None):
        """Handle row selection and show detail panel"""
        selected = self.tree.selection()
        if not selected:
            return
            
        # Get selected request ID
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
        
        # Update button state based on status
        self._update_assign_button()
        
        # Load and display full request details
        full_data = viewFull(self.selected_request_id)
        self._panel = MaintenanceDetailPanel(
            parent=self.detail_wrap,
            full_data=full_data,
            on_approve=self._approve,
            on_deny=self._deny,
            on_resolve=self._on_resolved,
        )
        
    def _update_assign_button(self):
        """Update Assign & Schedule button color and state based on request status"""
        if not self.selected_request_id or self.selected_request_id not in self.request_status:
            self.assign_btn.config(bg="#dc3545", state="disabled")
            return

        status = self.request_status[self.selected_request_id]
        
        if status == "Approved":
            # Approved - ready to assign (red, enabled)
            self.assign_btn.config(bg="#dc3545", state="normal")
        elif status == "In Progress":
            # Already assigned (green, disabled)
            self.assign_btn.config(bg="#28a745", state="disabled")
        else:
            # Open, Denied, or Resolved (red, disabled)
            self.assign_btn.config(bg="#dc3545", state="disabled")

    # ========================================================================
    # GUARD FUNCTIONS
    # ========================================================================

    def _require_selection(self):
        """Verify a request is selected"""
        if self.selected_request_id is None:
            messagebox.showerror("Selection Error", "Please select a request from the table first.")
            return False
        return True

    # ========================================================================
    # LIFECYCLE ACTIONS
    # ========================================================================

    def _assign_and_schedule(self):
        """Open staff assignment panel"""
        if not self._require_selection():
            return
        
        # Check status is approved
        status = self.request_status.get(self.selected_request_id)
        if status != "Approved":
            messagebox.showerror("Error", "Request must be approved before assignment.")
            return
            
        # Load full data and show assignment panel
        full_data = viewFull(self.selected_request_id)
        tenant_name = full_data[8] if full_data and len(full_data) > 8 else ""
        
        self._panel = StaffAssignmentPanel(
            parent=self.detail_wrap,
            request_id=self.selected_request_id,
            tenant_name=tenant_name,
            full_data=full_data,
            user_info=self.user_info,
            on_submit=self._on_staff_assigned_and_scheduled,
            on_cancel=self._on_row_select,
        )

    def _on_staff_assigned_and_scheduled(self, request_id, staff_name, comment):
        """Handle successful staff assignment"""
        messagebox.showinfo(
            "Success",
            f"Staff '{staff_name}' assigned and appointment scheduled for request #{request_id}.\n\n"
            f"Notification:\n{comment}",
        )
        self.request_status[request_id] = "In Progress"
        self._load_requests(reselect_id=request_id)

    def _approve(self):
        """Approve selected Open request"""
        if not self._require_selection():
            return
        try:
            result = update_request_status(self.selected_request_id, "approve")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not approve request:\n{e}")
            return
        if result:
            messagebox.showinfo("Approved", f"Request #{self.selected_request_id} has been approved.")
            self.request_status[self.selected_request_id] = "Approved"
            self._load_requests(reselect_id=self.selected_request_id)
        else:
            messagebox.showerror("Error", "Approval failed — no rows were updated.")

    def _deny(self):
        """Deny selected Open request"""
        if not self._require_selection():
            return
        try:
            result = update_request_status(self.selected_request_id, "reject")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not deny request:\n{e}")
            return
        if result:
            messagebox.showinfo("Denied", f"Request #{self.selected_request_id} has been denied.")
            self.request_status[self.selected_request_id] = "Denied"
            self._load_requests(reselect_id=self.selected_request_id)
        else:
            messagebox.showerror("Error", "Denial failed — no rows were updated.")

    def _on_resolved(self, notes, repair_time, repair_cost):
        """Mark request as resolved with details"""
        try:
            full_data = viewFull(self.selected_request_id)
            issue = full_data[7] if full_data and len(full_data) > 7 else ""
            
            result = resolve_request(
                request_id=self.selected_request_id,
                issue=issue,
                description=notes,
                repair_time=repair_time,
                repair_cost=repair_cost,
            )
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not resolve request:\n{e}")
            return
        if result:
            cost_text = f"£{repair_cost:.2f}" if repair_cost else "£0.00"
            time_text = f"{repair_time} hours" if repair_time else "0 hours"
            
            messagebox.showinfo(
                "Resolved",
                f"Request #{self.selected_request_id} marked as Resolved.\n"
                f"Repair Time: {time_text}\n"
                f"Repair Cost: {cost_text}\n"
                f"Notes: {notes}",
            )
            self.request_status[self.selected_request_id] = "Resolved"
            self._load_requests(reselect_id=self.selected_request_id)
        else:
            messagebox.showerror("Error", "Resolution failed — no rows were updated.")

    def _clear_form(self):
        """Clear form and deselect table row"""
        self.selected_request_id = None
        self._panel = None
        self.tree.selection_remove(self.tree.selection())
        self.assign_btn.config(bg="#dc3545", state="disabled")
        show_placeholder(self.detail_wrap, "Select a request to view details")
        self._load_requests()