# ============================================================================
# MAINTENANCE MAIN PAGE
# Request management page
# ============================================================================

import tkinter as tk
from tkinter import messagebox, ttk
from main.helpers import create_button, create_scrollable_treeview, show_placeholder

from modules.Request_Management import RegisterRequestPanel
from database.maintaince_service import (
    get_all_requests,
)


class MaintenancePage:
    """Maintenance request management page"""
    
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        
        # City filter for managers
        self._all_requests = []
        self._manager_city_filter_var = None
        self._manager_city_filter_cb = None
        
        # Main frames
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=(20, 20))
        
        # Build requests layout
        self.requests_frame = tk.Frame(self.content_frame, bg="#c9e4c4")
        self._init_requests_page()
        self.requests_frame.pack(fill="both", expand=True)

    def on_show(self):
        """Refresh requests when page/tab is shown."""
        self._load_requests()
    
    # ============================================================
    # REQUESTS PAGE
    # ============================================================
    def _init_requests_page(self):
        """Initialize Requests sub-page layout"""
        # Check if user is a manager
        is_manager = False
        if self.user_info and len(self.user_info) > 4:
            is_manager = (self.user_info[4] == "Manager")
        
        # City filter dropdown for managers only
        if is_manager:
            filter_frame = tk.Frame(self.requests_frame, bg="#c9e4c4")
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
            self._manager_city_filter_cb.bind("<<ComboboxSelected>>", lambda e: self._apply_city_filter())
        
        # Create table with appropriate columns
        if is_manager:
            # Manager view: include City column
            self._table_wrap, self.tree = create_scrollable_treeview(
                parent=self.requests_frame,
                columns=("id", "tenant", "issue", "date_submitted", "status", "city"),
                headings=("Request ID", "Tenant", "Issue", "Date Submitted", "Status", "City"),
                widths=(90, 140, 200, 120, 110, 100),
                anchors=("center", "w", "w", "center", "center", "center"),
            )
        else:
            # Non-manager view: no City column
            self._table_wrap, self.tree = create_scrollable_treeview(
                parent=self.requests_frame,
                columns=("id", "tenant", "issue", "date_submitted", "status"),
                headings=("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
                widths=(90, 160, 220, 140, 120),
                anchors=("center", "w", "w", "center", "center"),
            )
        
        # Bind row selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        
        # Detail panel with Add Request button
        self.detail_wrap = tk.Frame(self.requests_frame, bg="white", bd=2, relief="groove", height=100)
        self.detail_wrap.pack(fill="x", pady=(10, 0))
        self.detail_wrap.pack_propagate(False)  # Maintain fixed height
        
        # Button frame centered
        button_frame = tk.Frame(self.detail_wrap, bg="white")
        button_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # New Request button
        create_button(
            button_frame, text="✚ New Maintenance Request", width=250, height=55,
            bg="#28a745", fg="white", command=self._new_request
        ).pack()
        
        # Initialize tracking variables
        self.selected_request_id = None
        self._panel = None
        
        # Load requests
        self._load_requests()
    
    def _load_requests(self, reselect_id=None):
        """Load requests from database and populate table"""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        
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
            self._manager_city_filter_cb.set(current_selection)
        
        # Render request rows based on filter
        self._render_request_rows()
        
        # Reselect previously selected row if specified
        if reselect_id:
            for item in self.tree.get_children():
                if str(self.tree.item(item, "values")[0]) == str(reselect_id):
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    self.tree.see(item)
                    break
    
    def _apply_city_filter(self):
        """Apply city filter and refresh table"""
        if self._manager_city_filter_cb is not None:
            # Read directly from widget to avoid stale StringVar values.
            self._manager_city_filter_var.set(self._manager_city_filter_cb.get().strip())

        self._render_request_rows()
        
        # Clear selection when filter changes
        self.selected_request_id = None
        self.tree.selection_remove(self.tree.selection())

        # Reset detail area after changing filter.
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        self.detail_wrap.configure(height=100)
        self.detail_wrap.pack_configure(fill="x")
        self.detail_wrap.pack_propagate(False)

        button_frame = tk.Frame(self.detail_wrap, bg="white")
        button_frame.place(relx=0.5, rely=0.5, anchor="center")
        create_button(
            button_frame, text="✚ New Maintenance Request", width=250, height=55,
            bg="#28a745", fg="white", command=self._new_request
        ).pack()
    
    def _render_request_rows(self):
        """Render request rows based on current filter"""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Check if user is a manager
        is_manager = False
        if self.user_info and len(self.user_info) > 4:
            is_manager = (self.user_info[4] == "Manager")
        
        # Apply city filter for managers
        if is_manager and self._manager_city_filter_var:
            selected_city = self._manager_city_filter_var.get().strip()
            if not selected_city:
                selected_city = "All Cities"
            if selected_city == "All Cities":
                filtered_requests = self._all_requests
            else:
                # Filter by selected city (city is at index 5)
                filtered_requests = [
                    req for req in self._all_requests
                    if len(req) > 5 and str(req[5]).strip() == selected_city
                ]
        else:
            filtered_requests = self._all_requests
        
        # Insert filtered requests into table
        for row in filtered_requests:
            self.tree.insert("", "end", values=row)
    
    def _on_row_select(self, _event=None):
        """Handle row selection - just track the ID"""
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
    
    def _new_request(self):
        """Open new request registration form"""
        self.selected_request_id = None
        self.tree.selection_remove(self.tree.selection())
        
        # Clear detail area
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        
        # Allow detail wrap to expand for form
        self.detail_wrap.pack_propagate(True)
        
        # Show registration form
        self._panel = RegisterRequestPanel(
            parent=self.detail_wrap,
            user_info=self.user_info,
            on_submit=self._on_request_registered,
            on_cancel=self._clear_form,
        )
    
    def _on_request_registered(self, new_id):
        """Handle successful request registration"""
        messagebox.showinfo("Success", f"Maintenance request #{new_id} has been registered successfully.")
        self._load_requests(reselect_id=new_id)
        self._clear_form()
    
    def _clear_form(self):
        """Clear the form and refresh"""
        self.selected_request_id = None
        self._panel = None
        self.tree.selection_remove(self.tree.selection())
        
        # Clear detail area
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        
        # Reset to small fixed size
        self.detail_wrap.configure(height=100)
        self.detail_wrap.pack_configure(fill="x")
        self.detail_wrap.pack_propagate(False)
        
        # Button frame centered
        button_frame = tk.Frame(self.detail_wrap, bg="white")
        button_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        create_button(
            button_frame, text="✚ New Maintenance Request", width=250, height=55,
            bg="#28a745", fg="white", command=self._new_request
        ).pack()
        
        self._load_requests()
    
    # ============================================================
    # PAGE SWITCHING
    # ============================================================
    def show_requests_page(self):
        """Show requests page"""
        self.requests_frame.pack(fill="both", expand=True)


def create_page(parent, user_info):
    """Factory function to create a MaintenancePage instance"""
    page = MaintenancePage(parent, user_info)
    page.frame.on_show = page.on_show
    return page.frame