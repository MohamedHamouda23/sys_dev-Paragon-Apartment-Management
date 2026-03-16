import tkinter as tk

from database.tenant_service import get_tenant_payments
from main.helpers import create_button, create_scrollable_treeview, show_placeholder


class PaymentsPage:
    """Payments page with tenant-specific payment table."""

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.user_id = user_info[0] if user_info and len(user_info) >= 1 else None
        self.user_role = user_info[4] if user_info and len(user_info) >= 5 else None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.tree = None

        self._build_layout()
        self._load_payments()

    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        create_button(
            btns_inner_frame,
            text="Refresh Payments",
            width=180,
            height=45,
            bg="#3B86FF",
            fg="white",
            command=self._load_payments,
        ).pack(side="left", padx=8)

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))
        self.content_frame = content_frame

    def _load_payments(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if self.user_role != "Tenant":
            show_placeholder(self.content_frame, "Payments page is available for tenant accounts.")
            return

        if self.user_id is None:
            show_placeholder(self.content_frame, "Could not load user details for payments.")
            return

        rows = get_tenant_payments(self.user_id)

        if not rows:
            show_placeholder(self.content_frame, "No payment records found.")
            return

        _table_wrap, self.tree = create_scrollable_treeview(
            parent=self.content_frame,
            columns=("payment_id", "lease_id", "apartment", "due_date", "payment_date", "amount", "status", "is_late"),
            headings=("Payment ID", "Lease ID", "Apartment", "Due Date", "Payment Date", "Amount", "Status", "Late"),
            widths=(90, 90, 220, 120, 120, 110, 110, 90),
            anchors=("center", "center", "w", "center", "center", "e", "center", "center"),
            height=10,
        )

        for row in rows:
            self.tree.insert("", "end", values=row)


def create_page(parent, user_info=None):
    return PaymentsPage(parent, user_info=user_info).frame
