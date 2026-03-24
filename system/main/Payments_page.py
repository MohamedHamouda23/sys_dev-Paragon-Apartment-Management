# ID	Requirement Description	User Type / Role
# FR3.3	Record and flag late payments; apply late fees or penalties and show graph of late payments per property.	Finance Manager
# FR3.5	See payment history and download invoices.	Finance Manager / Tenants
# FR6.10	Make payments; system checks card and records payment.	Finance Manager / Tenants
# FR6.7	See own payment record and get alerts for late payments.	Finance Manager / Tenants
# ============================================================================
# PAYMENTS PAGE
# Main page for viewing and managing payments with role-based access
# ============================================================================

import tkinter as tk
from tkinter import ttk

from main.helpers import (
    create_button, clear_frame,
    styled_label, create_scrollable_treeview, show_placeholder,
    BG, FONT_LABEL
)

from database.tenant_service import get_tenant_payments
from database.payment_service import get_all_payments, get_payments_by_city


class PaymentsManagerPage:
    """Payments management page with role-based access control"""

    def __init__(self, parent, user_info=None):
        # Store parent and user info
        self.parent = parent
        self.user_info = user_info

        # Parse logged-in role and assigned city details
        self.user_id = user_info[0] if user_info and len(user_info) >= 1 else None
        self.user_role = user_info[4] if user_info and len(user_info) >= 5 else None
        self.assigned_city_name = user_info[3] if user_info and len(user_info) >= 4 else None
        self.user_city = user_info[5] if user_info and len(user_info) >= 6 else None
        
        self.is_finance_manager = self.user_role == "Finance Manager"
        self.is_coordinator = self.user_role == "Coordinator"
        self.is_tenant = self.user_role == "Tenant"

        self._all_payments = []
        self._city_filter_var = None
        self._city_filter_cb = None
        self.tree = None
        self.top_buttons = {}

        # Create main frame
        self.frame = tk.Frame(parent, bg="#c9e4c4")

        # Top button bar
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")
        self.btns_inner_frame = btns_inner_frame

        # Create action buttons
        self.create_buttons()

        # Content area for table
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))
        self.content_frame = content_frame

        # Load payments
        self.refresh_payments()

    # ========================================================================
    # CREATE BUTTONS
    # ========================================================================

    def create_buttons(self):
        """Create action buttons"""
        btn = create_button(
            self.btns_inner_frame,
            text="Refresh Payments",
            width=180,
            height=45,
            bg="#3B86FF",
            fg="white",
            command=self.refresh_payments,
            next_window_func=None,
            current_window=None
        )
        btn.pack(side="left", padx=8)
        self.top_buttons["Refresh"] = btn

    # ========================================================================
    # REFRESH PAYMENT LIST
    # ========================================================================

    def refresh_payments(self):
        """Load and display payments based on user role"""
        clear_frame(self.content_frame)

        # Validate user information
        if self.user_id is None or self.user_role is None:
            show_placeholder(self.content_frame, "Could not load user details for payments.")
            return

        # Load payments based on role
        rows = self._get_payments_by_role()
        self._all_payments = rows

        if not rows:
            show_placeholder(self.content_frame, "No payment records found.")
            return

        # Add city filter for Finance Manager
        if self.is_finance_manager:
            self._create_city_filter(rows)

        # Create table wrapper
        table_wrap = tk.Frame(self.content_frame, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, pady=(0, 12))

        # Determine columns based on role
        if self.is_tenant:
            columns = ("payment_id", "lease_id", "apartment", "due_date", "payment_date", "amount", "status", "is_late")
            headings = ("Payment ID", "Lease ID", "Apartment", "Due Date", "Payment Date", "Amount", "Status", "Late")
            widths = (90, 90, 220, 120, 120, 110, 110, 90)
            anchors = ("center", "center", "w", "center", "center", "e", "center", "center")
        else:  # Finance Manager or Coordinator
            columns = ("payment_id", "lease_id", "tenant_name", "apartment", "city", "due_date", "payment_date", "amount", "status", "is_late")
            headings = ("Payment ID", "Lease ID", "Tenant", "Apartment", "City", "Due Date", "Payment Date", "Amount", "Status", "Late")
            widths = (90, 80, 150, 180, 100, 110, 110, 100, 100, 70)
            anchors = ("center", "center", "w", "w", "center", "center", "center", "e", "center", "center")

        # Create table
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=10)

        # Set column headings
        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading)

        # Set column widths and anchors
        for col, width, anchor in zip(columns, widths, anchors):
            self.tree.column(col, width=width, anchor=anchor)

        # Add scrollbar
        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        # Pack table and scrollbar
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

        # Insert payment rows
        self._render_payment_rows()

    def _create_city_filter(self, rows):
        """Create city filter dropdown for Finance Manager"""
        search_wrap = tk.Frame(self.content_frame, bg="#c9e4c4")
        search_wrap.pack(fill="x", pady=(0, 10))

        tk.Label(search_wrap, text="City", bg="#c9e4c4", fg="#1f3b63", font=FONT_LABEL).pack(side="left", padx=(0, 10))

        # Extract unique cities from payment data (city is at index 4 for Finance Manager/Coordinator)
        city_options = ["All Cities"] + sorted({payment[4] for payment in rows if payment[4]})
        self._city_filter_var = tk.StringVar(value="All Cities")
        city_filter_cb = ttk.Combobox(
            search_wrap,
            textvariable=self._city_filter_var,
            values=city_options,
            state="readonly",
            width=24,
            font=("Arial", 11)
        )
        city_filter_cb.pack(side="left", padx=(0, 10), ipady=3)
        self._city_filter_cb = city_filter_cb
        city_filter_cb.bind("<<ComboboxSelected>>", lambda _e: self._run_city_filter(city_filter_cb.get()))

    def _run_city_filter(self, selected_city=None):
        """Apply Finance Manager city filter and refresh table rows"""
        if selected_city is None:
            if self._city_filter_cb is not None:
                selected_city = self._city_filter_cb.get()
            elif self._city_filter_var is not None:
                selected_city = self._city_filter_var.get()
            else:
                selected_city = "All Cities"

        selected_city = (selected_city or "All Cities").strip()
        
        if selected_city == "All Cities":
            self._all_payments = get_all_payments()
        else:
            all_rows = get_all_payments()
            # City is at index 4 in the Finance Manager/Coordinator view
            self._all_payments = [payment for payment in all_rows if str(payment[4]).strip() == selected_city]
        
        self._render_payment_rows()

    def _render_payment_rows(self):
        """Render payments in table"""
        if not self.tree:
            return

        self.tree.delete(*self.tree.get_children())

        for payment in self._all_payments:
            self.tree.insert("", "end", values=payment)

    def _get_payments_by_role(self):
        """Fetch payments based on user role"""
        if self.is_finance_manager:
            # Finance Manager: Full access to all payments across all cities
            return get_all_payments()
        
        elif self.is_coordinator:
            # Coordinator: Access only to payments in their specific city
            if self.user_city is None:
                return []
            return get_payments_by_city(self.user_city)
        
        elif self.is_tenant:
            # Tenant: Access only to their own payment records
            return get_tenant_payments(self.user_id)
        
        else:
            # Unknown role: no access
            return []


