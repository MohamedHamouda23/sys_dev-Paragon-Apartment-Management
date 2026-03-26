# Payments_page.py
import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import clear_frame, show_placeholder, create_scrollable_treeview, create_button
from database.payment_service import get_all_payments, get_tenant_payments, get_payment_details

class PaymentsPage:
    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.user_id = user_info[0] if user_info else None
        self.user_role = user_info[4] if user_info and len(user_info) >= 5 else None
        
        self._all_payments = []
        self.current_city = "All Cities"
        self.current_status = "All Status"

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self.refresh_payments()

    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))
        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        create_button(btns_inner_frame, text="Refresh Records", width=150, height=45,
            bg="#28a745", fg="white", command=self.refresh_payments).pack(side="left", padx=8)

        create_button(btns_inner_frame, text="Reset Filters", width=110, height=45,
            bg="#3B86FF", fg="white", command=self._reset_filters).pack(side="left", padx=8)

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        filter_frame = tk.Frame(content_frame, bg="#c9e4c4")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        if self.user_role == "Finance Manager":
            tk.Label(filter_frame, text="City:", bg="#c9e4c4", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
            self.city_cb = ttk.Combobox(filter_frame, state="readonly", width=15)
            self.city_cb.pack(side="left", padx=(0, 15))
            self.city_cb.bind("<<ComboboxSelected>>", lambda e: self._update_filter("city", self.city_cb.get()))
        
        tk.Label(filter_frame, text="Status:", bg="#c9e4c4", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
        self.status_cb = ttk.Combobox(filter_frame, values=["All Status", "Paid", "Pending", "Unpaid"], state="readonly", width=12)
        self.status_cb.set(self.current_status)
        self.status_cb.pack(side="left", padx=(0, 15))
        self.status_cb.bind("<<ComboboxSelected>>", lambda e: self._update_filter("status", self.status_cb.get()))

        is_fm = self.user_role == "Finance Manager"
        cols = ("name", "apt", "city", "due", "paid", "amt", "stat", "late") if is_fm else ("apt", "due", "paid", "amt", "stat", "late")
        heads = ("Tenant", "Apt", "City", "Due Date", "Paid Date", "Amount", "Status", "Late") if is_fm else ("Apartment", "Due Date", "Paid Date", "Amount", "Status", "Late")
        widths = (120, 150, 90, 100, 100, 80, 110, 60) if is_fm else (220, 110, 110, 90, 130, 70)

        _, self.tree = create_scrollable_treeview(content_frame, cols, heads, widths, ["center"]*len(cols), height=12)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a payment record to view full details")

    def refresh_payments(self):
        if self.user_role == "Finance Manager":
            self._all_payments = get_all_payments() or []
            cities = ["All Cities"] + sorted(list(set(str(p[2]) for p in self._all_payments if p[2])))
            self.city_cb['values'] = cities
            self.city_cb.set(self.current_city)
        else:
            self._all_payments = get_tenant_payments(self.user_id) or []
        self._render_rows()

    def _render_rows(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for p in self._all_payments:
            if self.user_role == "Finance Manager":
                if self.current_city != "All Cities" and str(p[2]) != self.current_city: continue
            
            if self.current_status != "All Status" and self.current_status not in str(p[6 if self.user_role=="Finance Manager" else 5]): continue
            
            p_id = p[-1] 
            self.tree.insert("", "end", values=p[:-1], tags=(p_id,))

    def _on_row_select(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        p_id = self.tree.item(sel[0])["tags"][0]
        self._render_lifecycle_detail(p_id)

    def _render_lifecycle_detail(self, p_id):
        clear_frame(self.detail_wrap)
        details = get_payment_details(p_id)
        if not details: return
        container = tk.Frame(self.detail_wrap, bg="#f0f2f5")
        container.pack(fill="both", expand=True, padx=15, pady=10)
        
        tk.Label(container, text=f"PAYMENT BREAKDOWN #{details['payment_id']} - {details['status']}", bg="white", font=("Arial", 10, "bold")).pack()
        tk.Label(container, text=f"Tenant: {details['tenant_name']} | Amount Paid: £{details['paid_amount']} / £{details['agreed_rent']}", bg="#f0f2f5").pack()

    def _update_filter(self, key, val):
        if key == "city": self.current_city = val
        elif key == "status": self.current_status = val
        self._render_rows()

    def _reset_filters(self):
        self.current_city = "All Cities"
        self.current_status = "All Status"
        if hasattr(self, 'city_cb'): self.city_cb.set("All Cities")
        self.status_cb.set("All Status")
        self._render_rows()

    def get_frame(self): return self.frame