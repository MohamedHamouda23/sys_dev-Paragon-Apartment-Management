# ============================================================================
# REQUEST MANAGEMENT PAGE
# Main page for viewing and creating maintenance requests
# ============================================================================

import tkinter as tk
from tkinter import messagebox
from database.maintaince_service import get_all_requests
from main.helpers import create_button, create_scrollable_treeview, show_placeholder

from modules.Request_Management import RegisterRequestPanel


class RequestManagementPage:
    """Request management page with table and registration form"""

    def __init__(self, parent, user_info=None):
        # Store parent and user info
        self.parent              = parent
        self.user_info           = user_info
        self.selected_request_id = None
        self._panel              = None
        
        # Create main frame
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        
        # Build UI components
        self._build_layout()
        self._load_requests()

    # ========================================================================
    # BUILD LAYOUT
    # ========================================================================
    def on_show(self):
        """Called when page becomes visible - refresh data"""
        print("Request Management page shown - refreshing data")
        self._load_requests()

    def _build_layout(self):
        """Create the page layout with buttons, table, and detail panel"""
        # Top button bar
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        # Create action buttons
        for text, cmd, w in [
            ("New Request",          self._new_request, 140),
            ("Clear Form",           self._clear_form,  110),
        ]:
            create_button(
                btns_inner_frame, text=text, width=w, height=45,
                bg="#3B86FF", fg="white", command=cmd,
            ).pack(side="left", padx=8)

        # Content area with table and detail panel
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        # Create scrollable table
        _table_wrap, self.tree = create_scrollable_treeview(
            parent   = content_frame,
            columns  = ("id", "tenant", "issue", "date_submitted", "status"),
            headings = ("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
            widths   = (90, 160, 220, 140, 120),
            anchors  = ("center", "w", "w", "center", "center"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Detail panel (form area)
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a request or create a new one")

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def _load_requests(self, reselect_id=None):
        """Load requests into table from database (filtered by user's city)"""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Insert request rows (filtered by user's city)
        for row in (get_all_requests(user_info=self.user_info) or []):
            self.tree.insert("", "end", values=row)

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
        """Handle row selection in table"""
        selected = self.tree.selection()
        if not selected:
            return
            
        # Get selected request data
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
        
        # Show selection message
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        show_placeholder(self.detail_wrap, f"Request #{self.selected_request_id} selected")

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def _new_request(self):
        """Open registration form for new request"""
        # Deselect any row
        self.selected_request_id = None
        self.tree.selection_remove(self.tree.selection())
        
        # Show registration form
        self._panel = RegisterRequestPanel(
            parent    = self.detail_wrap,
            user_info = self.user_info,
            on_submit = self._on_request_registered,
            on_cancel = self._clear_form,
        )

    def _on_request_registered(self, new_id):
        """Handle successful request registration"""
        messagebox.showinfo(
            "Success",
            f"Maintenance request #{new_id} has been registered successfully.",
        )
        self._load_requests(reselect_id=new_id)

    def _clear_form(self):
        """Clear form and deselect table row"""
        self.selected_request_id = None
        self._panel              = None
        self.tree.selection_remove(self.tree.selection())
        show_placeholder(self.detail_wrap, "Select a request or create a new one")
        self._load_requests()


