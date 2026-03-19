# ============================================================================
# LIFECYCLE PAGE - MAINTENANCE MANAGEMENT
# Main page for managing maintenance request lifecycle
# ============================================================================

import tkinter as tk
from tkinter import messagebox, ttk
from main.helpers import create_button, create_scrollable_treeview, show_placeholder
from database.maintaince_service import get_all_requests, viewFull, update_request_status, resolve_request

from modules.Lifecycle_Management import (
    StaffAssignmentPanel,
    MaintenanceDetailPanel,
)


class MaintenanceManagementPage:
    """Main page for maintenance request lifecycle management"""
    
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.selected_request_id = None
        self._panel = None
        self.request_status = {}
        self._all_requests = []  # Store all requests for filtering
        self._manager_city_filter_var = None
        self._manager_city_filter_cb = None
        
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self._load_requests()

    def on_show(self):
        """Refresh data when page is shown"""
        self.refresh_data()

    def refresh_data(self):
        """Refresh all data and clear selection"""
        self._load_requests()
        self.selected_request_id = None
        self._panel = None
        self.tree.selection_remove(self.tree.selection())
        self.assign_btn.config(bg="#dc3545", state="disabled")
        
        # Clear detail panel
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        show_placeholder(self.detail_wrap, "Select a request to view details")

    def _build_layout(self):
        """Build the page layout"""
        # Top button frame
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        # Assign & Schedule button (disabled by default)
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

        # Main content frame
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        # Check if user is a manager
        is_manager = False
        if self.user_info and len(self.user_info) > 4:
            is_manager = (self.user_info[4] == "Manager")
        
        # City filter dropdown for managers only
        if is_manager:
            filter_frame = tk.Frame(content_frame, bg="#c9e4c4")
            filter_frame.pack(fill="x", pady=(0, 10))
            
            tk.Label(
                filter_frame, text="Filter by City:", bg="#c9e4c4", 
                fg="#1f3b63", font=("Arial", 10, "bold")
            ).pack(side="left", padx=(0, 10))
            
            # City filter combobox
            self._manager_city_filter_var = tk.StringVar(value="All Cities")
            self._manager_city_filter_cb = ttk.Combobox(
                filter_frame,
                textvariable=self._manager_city_filter_var,
                values=["All Cities"],
                state="readonly",
                width=20,
                font=("Arial", 10)
            )
            self._manager_city_filter_cb.pack(side="left", padx=(0, 10))
            self._manager_city_filter_cb.bind("<<ComboboxSelected>>", self._apply_city_filter)        
        # Create table with appropriate columns
        if is_manager:
            # Manager view: include City column
            _table_wrap, self.tree = create_scrollable_treeview(
                parent=content_frame,
                columns=("id", "tenant", "issue", "date_submitted", "status", "city"),
                headings=("Request ID", "Tenant", "Issue", "Date Submitted", "Status", "City"),
                widths=(90, 140, 200, 120, 110, 100),
                anchors=("center", "w", "w", "center", "center", "center"),
            )
        else:
            # Non-manager view: no City column
            _table_wrap, self.tree = create_scrollable_treeview(
                parent=content_frame,
                columns=("id", "tenant", "issue", "date_submitted", "status"),
                headings=("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
                widths=(90, 160, 220, 140, 120),
                anchors=("center", "w", "w", "center", "center"),
            )
        
        # Bind row selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Detail panel
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a request to view details")

    def _load_requests(self, reselect_id=None):
        """Load requests from database and populate table"""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        self.request_status.clear()
        
        # Get all requests from database
        requests = get_all_requests(user_info=self.user_info) or []
        self._all_requests = requests  # Store for filtering
        
        # Check if user is a manager
        is_manager = False
        if self.user_info and len(self.user_info) > 4:
            is_manager = (self.user_info[4] == "Manager")
        
        # Populate city filter dropdown for managers
        if is_manager and self._manager_city_filter_cb:
            # Extract unique cities from requests (city is at index 5)
            city_options = ["All Cities"] + sorted({req[5] for req in requests if len(req) > 5 and req[5]})
            self._manager_city_filter_cb['values'] = city_options
            
            # Keep current selection if valid
            current_selection = self._manager_city_filter_var.get() if self._manager_city_filter_var else "All Cities"
            if current_selection not in city_options:
                current_selection = "All Cities"
            self._manager_city_filter_var.set(current_selection)
        
        # Render request rows based on filter
        self._render_request_rows()

        # Reselect previously selected row if specified
        if reselect_id is not None:
            for item in self.tree.get_children():
                if str(self.tree.item(item, "values")[0]) == str(reselect_id):
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    break
    
    def _apply_city_filter(self, event=None): # Added event=None
        """Apply city filter and refresh table"""
        # Force get the current value from the widget directly
        selected = self._manager_city_filter_cb.get()
        self._manager_city_filter_var.set(selected)
                
        self._render_request_rows()
        
        # Reset selection state
        self.selected_request_id = None
        self.tree.selection_remove(self.tree.selection())
        self.assign_btn.config(bg="#dc3545", state="disabled")
        
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        show_placeholder(self.detail_wrap, "Select a request to view details")

    def _render_request_rows(self):
        """Render request rows based on current filter"""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        self.request_status.clear()

        # For non-managers, default to "All Cities"
        if self._manager_city_filter_var is not None:
            selected_city = self._manager_city_filter_var.get()
        else:
            selected_city = "All Cities"

        # Filter logic
        if selected_city == "All Cities":
            filtered_requests = self._all_requests
        else:
            filtered_requests = [
                req for req in self._all_requests 
                if len(req) > 5 and str(req[5]).strip() == selected_city.strip()
            ]
        
        for row in filtered_requests:
            self.tree.insert("", "end", values=row)
            self.request_status[str(row[0])] = row[4]

    def _on_row_select(self, _event=None):
        """Handle row selection event"""
        selected = self.tree.selection()
        if not selected: 
            return
            
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
        self._update_assign_button()
        
        # Load full details and show detail panel
        full_data = viewFull(self.selected_request_id)
        self._panel = MaintenanceDetailPanel(
            parent=self.detail_wrap,
            full_data=full_data,
            on_approve=self._approve,
            on_deny=self._deny,
            on_resolve=self._on_resolved,
            on_update_priority=self._refresh_after_priority_change,
            user_info=self.user_info
        )

    def _refresh_after_priority_change(self, request_id):
        """Refresh data without losing current selection"""
        self._load_requests(reselect_id=request_id)
        self._on_row_select() 

    def _update_assign_button(self):
        """Update assign button state based on request status"""
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
        """Open staff assignment panel"""
        if not self.selected_request_id: 
            return
        
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
        """Handle successful staff assignment"""
        messagebox.showinfo("Success", f"Staff assigned to #{request_id}")
        self._load_requests(reselect_id=request_id)
        self._on_row_select()

    def _approve(self, request_id=None):
        """Approve a maintenance request"""
        target_id = request_id if request_id else self.selected_request_id
        if not target_id: 
            return

        if update_request_status(target_id, "approve"):
            messagebox.showinfo("Approved", f"Request #{target_id} approved.")
            self._load_requests(reselect_id=target_id)
            self._on_row_select()
        else:
            messagebox.showerror("Error", "Approval failed.")

    def _deny(self, request_id=None):
        """Deny a maintenance request"""
        target_id = request_id if request_id else self.selected_request_id
        if not target_id: 
            return

        if update_request_status(target_id, "reject"):
            messagebox.showinfo("Denied", f"Request #{target_id} denied.")
            self._load_requests(reselect_id=target_id)
            self._on_row_select()
        else:
            messagebox.showerror("Error", "Denial failed.")

    def _on_resolved(self, notes, repair_cost, repair_time):
        """Handle request resolution"""
        if resolve_request(self.selected_request_id, notes, repair_cost, repair_time):
            messagebox.showinfo("Resolved", "Request marked as Resolved.")
            self._load_requests(reselect_id=self.selected_request_id)
            self._on_row_select()

    def _clear_form(self):
        """Clear form and refresh data"""
        self.refresh_data()