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
        
        create_button(self.frame, "Make Payment", command=self._pay).pack(pady=10)

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

    def _render_lifecycle_detail(self, details):
        clear_frame(self.detail_container)
        
        # FIX: If payment_date is missing, paid amount is strictly 0.00
        p_date = details.get('payment_date')
        if not p_date or p_date in ["-", "N/A", "None"]:
            paid_amount = 0.0
        else:
            paid_amount = float(details.get('paid_amount') or 0)
            
        rent = float(details.get('agreed_rent') or 0)
        outstanding = max(rent - paid_amount, 0)
        status = details.get('status', 'Unpaid')

        tk.Label(self.detail_container, text="Payment Lifecycle", font=("Arial", 12, "bold"), bg="white").pack(pady=15)
        
        color = "#e74c3c" if status == "Unpaid" else "#f39c12" if "Partial" in status else "#27ae60"
        tk.Label(self.detail_container, text=status.upper(), fg="white", bg=color, font=("Arial", 9, "bold"), padx=10).pack(pady=5)

        info_f = tk.Frame(self.detail_container, bg="white")
        info_f.pack(fill="x", padx=20, pady=10)

        tk.Label(info_f, text=f"Agreed Rent: £{rent:.2f}", bg="white").pack(anchor="w")
        tk.Label(info_f, text=f"Paid to Date: £{paid_amount:.2f}", bg="white", fg="green").pack(anchor="w")
        tk.Label(info_f, text=f"Outstanding: £{outstanding:.2f}", bg="white", fg="red", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5,0))

        if self.user_role == "Tenant" and outstanding > 0.01:
            create_button(self.detail_container, "Make Payment", command=self._open_payment_gateway, bg="#27ae60", fg="white").pack(pady=20)

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
