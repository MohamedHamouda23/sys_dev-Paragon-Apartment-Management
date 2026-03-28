# Payments_page.py
import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_scrollable_treeview, create_button
from database.tenant_portal_service import get_tenant_payments_with_balance
from main.PaymentGateway import PaymentWindow

class PaymentsPage:
    def __init__(self, parent, user_info):
        self.user_id = user_info[0]
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self.refresh_payments()

    def _build_layout(self):
        filter_f = tk.Frame(self.frame, bg="#c9e4c4")
        filter_f.pack(fill="x", pady=10)

        # Lease Filter
        tk.Label(filter_f, text="Lease:").pack(side="left", padx=5)
        self.lease_cb = ttk.Combobox(filter_f, state="readonly", width=15)
        self.lease_cb.pack(side="left", padx=5)
        self.lease_cb.bind("<<ComboboxSelected>>", lambda e: self._render_rows())

        # Status Filter
        tk.Label(filter_f, text="Status:").pack(side="left", padx=5)
        self.status_cb = ttk.Combobox(filter_f, values=["All", "Paid", "Unpaid"], state="readonly", width=10)
        self.status_cb.set("All")
        self.status_cb.pack(side="left", padx=5)
        self.status_cb.bind("<<ComboboxSelected>>", lambda e: self._render_rows())

        self.tree = create_scrollable_treeview(self.frame, ["ID", "Property", "Due Date", "Paid", "Total", "Status"])
        self.tree.pack(fill="both", expand=True, padx=20)
        
        create_button(self.frame, "Make Payment", command=self._pay).pack(pady=(10, 30))

    def refresh_payments(self):
        self.data = get_tenant_payments_with_balance(self.user_id)
        leases = sorted(list(set(d['property'] for d in self.data)))
        self.lease_cb['values'] = ["All"] + leases
        self.lease_cb.set("All")
        self._render_rows()

    def _render_rows(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        l_filt = self.lease_cb.get()
        s_filt = self.status_cb.get()

        for d in self.data:
            if l_filt != "All" and d['property'] != l_filt: continue
            if s_filt != "All" and d['status'] != s_filt: continue
            self.tree.insert("", "end", values=(d['payment_id'], d['property'], d['due_date'], d['paid_amount'], d['agreed_rent'], d['status']))

    def _on_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        self.selected_payment_id = item['values'][-1]
        details = get_payment_details(self.selected_payment_id)
        if details:
            self._render_lifecycle_detail(details)

    def _render_lifecycle_detail_panel(self, payment_id, details):
        clear_frame(self.detail_wrap)

        # 1. Main container for the white box
        # Use a small bottom pady here; the spacer handles the large gap
        container = tk.Frame(self.detail_wrap, bg="#f0f2f5")
        container.pack(fill="x", padx=15, pady=(10, 0))

        # --- Header ---
        header = tk.Frame(container, bg="white", bd=1, relief="solid")
        header.pack(fill="x", pady=(0, 5))

        tk.Label(
            header,
            text=f"TRANSACTION MANAGEMENT: #{payment_id}",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#1f3b63",
        ).pack(side="left", padx=15, pady=8)

        # Logic for calculations
        agreed = float(details.get("agreed_rent", 0) or 0)
        p_date = details.get("payment_date")
        raw_paid = float(details.get("paid_amount", 0) or 0)
        paid = 0.0 if not p_date or p_date in ["-", "None", "N/A"] else raw_paid
        outstanding = max(agreed - paid, 0)
        badge_bg = "#27ae60" if paid >= agreed else "#e74c3c"
        status_text = "PAID" if paid >= agreed else "UNPAID"

        tk.Label(
            header,
            text=status_text,
            bg=badge_bg,
            fg="white",
            font=("Arial", 8, "bold"),
            padx=12,
            pady=2,
        ).pack(side="right", padx=15)

        # --- Info Cards ---
        cols_frame = tk.Frame(container, bg="#f0f2f5")
        cols_frame.pack(fill="x")

        sections = [
            ("Occupant Info", [("Tenant", details.get("tenant_name")), ("Property", details.get("property")), ("Location", details.get("city"))]),
            ("Billing Period", [("Due Date", details.get("due_date")), ("Paid Date", p_date if p_date else "-"), ("Late status", details.get("is_late", "No"))]),
            ("Financial Breakdown", [("Expected", f"£{agreed:.2f}"), ("Actual Paid", f"£{paid:.2f}"), ("Outstanding", f"£{outstanding:.2f}")])
        ]

        for title, items in sections:
            card = tk.Frame(cols_frame, bg="white", bd=1, relief="solid")
            card.pack(side="left", fill="both", expand=True, padx=2)
            tk.Label(card, text=title, font=("Arial", 9, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w", padx=10, pady=(5, 2))
            for key, value in items:
                row = tk.Frame(card, bg="white")
                row.pack(fill="x", padx=10, pady=1)
                tk.Label(row, text=f"{key}:", font=("Arial", 8), bg="white").pack(side="left")
                tk.Label(row, text=str(value), font=("Arial", 8, "bold"), bg="white").pack(side="right")

        # --- Footer (Buttons) ---
        footer = tk.Frame(container, bg="#f0f2f5")
        footer.pack(fill="x", pady=(15, 15)) 

        create_button(
            footer, "Generate PDF Invoice", 160, 35, "#1f3b63", "white", 
            lambda: self._download_invoice(details)
        ).pack(side="left")

        if self.user_role == "Tenant" and outstanding > 0.01:
            create_button(
                footer, "Pay Now", 140, 35, "#28a745", "white", 
                lambda: PaymentWindow(self.frame.winfo_toplevel(), self.user_id, payment_id, outstanding, self.refresh_payments)
            ).pack(side="left", padx=15)

        # --- THE FIX: BOTTOM SPACER ---
        # This frame matches your background color (#c9e4c4) and adds 60px of height.
        # This forces the scrollable area to show empty space at the very start of the scroll.
        bottom_spacer = tk.Frame(self.detail_wrap, bg="#c9e4c4", height=60)
        bottom_spacer.pack(fill="x")

    def _open_payment_gateway(self):
        details = get_payment_details(self.selected_payment_id)
        p_date = details.get('payment_date')
        rent = float(details.get('agreed_rent') or 0)
        
        # FIX: Force 0 if Unpaid so gateway calculates full rent as outstanding
        paid = 0.0 if not p_date or p_date in ["-", "N/A"] else float(details.get('paid_amount') or 0)
        outstanding = round(rent - paid, 2)
        
        if outstanding <= 0:
            messagebox.showinfo("Info", "This rent is already fully paid.")
            return

        PaymentWindow(self.frame.winfo_toplevel(), self.user_id, self.selected_payment_id, outstanding, self.refresh_payments)
        
    def _update_filter(self, key, val):
        if key == "status": self.current_status = val
        self._render_rows()

    def _reset_filters(self):
        self.current_city = "All Cities"
        self.current_status = "All Status"
        if hasattr(self, 'city_cb'): 
            self.city_cb.set("All Cities")
        self.status_cb.set("All Status")
        self._render_rows()

    def get_frame(self): 
        return self.frame
