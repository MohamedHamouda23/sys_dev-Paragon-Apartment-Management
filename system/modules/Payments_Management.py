import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from main.helpers import create_button, clear_frame, show_placeholder, create_scrollable_treeview
from database.payment_service import get_all_payments, get_tenant_payments, get_payment_details
from database.tenant_portal_service import (
    get_neighbor_comparison,
    get_tenant_payments_with_balance,
    get_payment_history_series,
    get_late_payment_by_property
)



from main.PaymentGateway import PaymentWindow


class PaymentsManagementPage:
    def __init__(self, parent, user_info=None):
        self.parent, self.user_info = parent, user_info
        self.user_id = user_info[0] if user_info else None
        self.user_role = user_info[4] if user_info and len(user_info) >= 5 else None
        self._all_payments = []
        
        self.current_city = "All Cities"
        self.current_status = "All Status"
        self.current_range = "All Time"
        self.current_late = "All (Late/On-Time)"
        self.show_graphs = True
        self.show_graph_btn = None
        self.hide_graph_btn = None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self.refresh_payments()

    def _build_layout(self):
        top_bar = tk.Frame(self.frame, bg="#c9e4c4")
        top_bar.pack(side="top", fill="x", pady=(20, 10))
        
        btns_inner = tk.Frame(top_bar, bg="#c9e4c4")
        btns_inner.pack(anchor="center")

        
        create_button(btns_inner, "Refresh", 120, 45, "#3B86FF", "white", 
                  self.refresh_payments).pack(side="left", padx=10)

        if self.user_role == "Tenant":
            self.show_graph_btn = create_button(
                btns_inner,
                "Show Graphs",
                120,
                45,
                "#28a745",
                "white",
                lambda: self._set_graph_visibility(True),
            )
            self.show_graph_btn.pack(side="left", padx=10)

            self.hide_graph_btn = create_button(
                btns_inner,
                "Hide Graphs",
                120,
                45,
                "#dc3545",
                "white",
                lambda: self._set_graph_visibility(False),
            )
            self.hide_graph_btn.pack(side="left", padx=10)
            self._update_graph_toggle_buttons()

        self.content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        self.content_frame.pack(fill="both", expand=True, padx=20)

        self.detail_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=20, pady=20)
        show_placeholder(self.detail_wrap, "Select a payment record to view the Lifecycle breakdown")

    def _download_invoice(self, details):
        p_id = details.get('payment_id', 'N/A')
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Invoice_{details.get('tenant_name', 'User')}_{p_id}.pdf",
            title="Save PDF Invoice",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path: return

        try:
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4

            # --- HEADER ---
            c.setFillColor(colors.HexColor("#1f3b63"))
            c.rect(0, height - 80, width, 80, fill=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, height - 50, "OFFICIAL PAYMENT INVOICE")

            # --- INVOICE INFO ---
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 120, f"Invoice Ref: #{p_id}")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 135, f"Date Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")

            # --- TENANT DETAILS ---
            c.line(50, height - 150, width - 50, height - 150)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 175, "BILL TO:")
            c.setFont("Helvetica", 11)
            c.drawString(50, height - 190, f"Tenant Name: {details.get('tenant_name', 'N/A')}")
            c.drawString(50, height - 205, f"Property: {details.get('property', 'N/A')}")
            c.drawString(50, height - 220, f"City: {details.get('city', 'N/A')}")

            # --- TABLE DATA ---
            c.setFillColor(colors.HexColor("#f0f2f5"))
            c.rect(50, height - 300, width - 100, 30, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(60, height - 280, "Description")
            c.drawRightString(width - 60, height - 280, "Amount")
            
            c.setFont("Helvetica", 11)
            c.drawString(60, height - 320, f"Rent Payment for Due Date: {details.get('due_date', 'N/A')}")
            c.drawRightString(width - 60, height - 320, f"GBP {details.get('paid_amount', '0.00')}")

            # --- TOTAL ---
            c.line(width - 200, height - 350, width - 50, height - 350)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(width - 200, height - 375, "TOTAL PAID:")
            c.drawRightString(width - 60, height - 375, f"£{details.get('paid_amount', '0.00')}")

            # --- FOOTER ---
            c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(width/2, 50, "Thank you for your prompt payment. This is a computer-generated document.")

            c.save()
            messagebox.showinfo("Success", f"PDF Invoice saved successfully at:\n{file_path}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to generate PDF: {str(e)}")

    def refresh_payments(self):
        if self.user_role == "Finance Manager":
            self._all_payments = get_all_payments() or []
        elif self.user_role == "Tenant":
            tenant_rows = get_tenant_payments_with_balance(self.user_id) or []
            self._all_payments = [
                (
                    row["property"],
                    row["due_date"],
                    row["payment_date"],
                    row["paid_amount"],
                    row["agreed_rent"],
                    row["status"],
                    row.get("is_late", 0),
                    row["payment_id"],
                )
                for row in tenant_rows
            ]
        else:
            self._all_payments = get_tenant_payments(self.user_id) or []
        self._render_view()

    def _render_view(self):
        clear_frame(self.content_frame)
        is_fm = self.user_role == "Finance Manager"
        
        f_bar = tk.Frame(self.content_frame, bg="#c9e4c4")
        f_bar.pack(fill="x", pady=(0, 10))

        # --- Existing Period Filter ---
        tk.Label(f_bar, text="Period:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left")
        cb_r = ttk.Combobox(f_bar, values=["All Time", "Last Month", "Last 3 Months"], state="readonly", width=15)
        cb_r.set(self.current_range)
        cb_r.pack(side="left", padx=5)
        cb_r.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "range"))
        
        if is_fm:
            # --- Existing City Filter ---
            tk.Label(f_bar, text="City:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 0))
            cities = ["All Cities"] + sorted({p[2] for p in self._all_payments if len(p) > 2 and p[2]})
            cb_c = ttk.Combobox(f_bar, values=cities, state="readonly", width=15)
            cb_c.set(self.current_city)
            cb_c.pack(side="left", padx=5)
            cb_c.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "city"))

            # --- NEW: Late Status Filter ---
            tk.Label(f_bar, text="Late Status:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 0))
            # Assuming you add self.current_late to __init__ (e.g., set to "All")
            cb_l = ttk.Combobox(f_bar, values=["All", "Late Only", "On-Time Only"], state="readonly", width=15)
            cb_l.set(getattr(self, 'current_late', 'All')) 
            cb_l.pack(side="left", padx=5)
            cb_l.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "late"))

        if self.user_role == "Tenant" and self.show_graphs:
            graphs_wrap = tk.Frame(self.content_frame, bg="#c9e4c4")
            graphs_wrap.pack(fill="both", expand=False, pady=(0, 10))

            self.chart_payment = self._chart_card(graphs_wrap, "Payment History")
            self.chart_late = self._chart_card(graphs_wrap, "Late Payments Per Property")
            self.chart_compare = self._chart_card(graphs_wrap, "You vs Neighbours")

            self._draw_line_chart(self.chart_payment, get_payment_history_series(self.user_id))
            self._draw_bar_chart(self.chart_late, get_late_payment_by_property(self.user_id))
            cmp_data = get_neighbor_comparison(self.user_id)
            self._draw_compare_chart(
                self.chart_compare,
                cmp_data.get("tenant_avg", 0),
                cmp_data.get("neighbor_avg", 0),
            )

        # --- Treeview Configuration ---
        cols = ("tenant", "unit", "city", "due", "paid_dt", "paid_amt", "agreed", "stat", "late") if is_fm else             ("unit", "due", "paid_dt", "paid_amt", "agreed", "stat", "late")
        heads = ("Tenant", "Unit", "City", "Due Date", "Paid Date", "Paid", "Agreed", "Status", "Late") if is_fm else                 ("Unit", "Due Date", "Paid Date", "Paid", "Agreed", "Status", "Late")
        widths = (120, 140, 100, 100, 100, 80, 80, 120, 60) if is_fm else (220, 110, 110, 90, 90, 130, 70)

        table_wrap = tk.Frame(self.content_frame, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, pady=(0, 12))
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", height=12)
        for c, h, w in zip(cols, heads, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        y_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=(8, 0))
        x_scroll.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_row_select())
        
        for r in self._all_payments:
            p_id = r[-1]
            
            # Filter by City
            if is_fm and self.current_city != "All Cities" and r[2] != self.current_city: 
                continue
            
            # NEW: Filter by Late Status (r[8] is the 'late' column in the FM query)
            if is_fm:
                late_filter = getattr(self, 'current_late', 'All')
                is_late_value = r[8] # "Yes" or "No"
                if late_filter == "Late Only" and is_late_value != "Yes":
                    continue
                if late_filter == "On-Time Only" and is_late_value != "No":
                    continue

            self.tree.insert("", "end", values=r[:len(cols)], tags=(p_id,))

    def _on_row_select(self):
        sel = self.tree.selection()
        if not sel: return
        p_id = self.tree.item(sel[0])["tags"][0]
        details = get_payment_details(p_id)
        if not details: return
        self._render_lifecycle_detail_panel(p_id, details)
        
    def _render_lifecycle_detail_panel(self, p_id, details):
        clear_frame(self.detail_wrap)

        container = tk.Frame(self.detail_wrap, bg="#f0f2f5")
        container.pack(fill="both", expand=True, padx=15, pady=10)

        # HEADER
        header = tk.Frame(container, bg="white", bd=1, relief="solid")
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text=f"TRANSACTION MANAGEMENT: #{p_id}",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#1f3b63"
        ).pack(side="left", padx=15, pady=10)

        # 🔥 IMPORTANT: use correct paid logic
        agreed = float(details.get('agreed_rent', 0))

        payment_date = details.get("payment_date")
        raw_paid = float(details.get("paid_amount", 0))

        # ✅ FIX: unpaid = 0 always
        if not payment_date or payment_date in ["-", "None", "N/A"]:
            paid = 0.0
        else:
            paid = raw_paid

        diff = max(agreed - paid, 0)

        # STATUS
        if paid == 0:
            status_text = "UNPAID"
            badge_bg = "#e74c3c"
        elif paid < agreed:
            status_text = "PARTIAL"
            badge_bg = "#f39c12"
        else:
            status_text = "PAID"
            badge_bg = "#27ae60"

        tk.Label(
            header,
            text=status_text,
            bg=badge_bg,
            fg="white",
            font=("Arial", 8, "bold"),
            padx=12,
            pady=2
        ).pack(side="right", padx=15)

        # BODY
        cols_frame = tk.Frame(container, bg="#f0f2f5")
        cols_frame.pack(fill="x")

        sections = [
            ("Occupant Info", [
                ("Tenant", details.get('tenant_name')),
                ("Property", details.get('property')),
                ("Location", details.get('city', 'N/A'))
            ]),
            ("Billing Period", [
                ("Due Date", details.get('due_date')),
                ("Paid Date", payment_date if payment_date else "-"),
                ("Late status", details.get('is_late', 'No'))
            ]),
            ("Financial Breakdown", [
                ("Expected", f"£{agreed:.2f}"),
                ("Actual Paid", f"£{paid:.2f}"),   # ✅ FIXED
                ("Outstanding", f"£{diff:.2f}")
            ])
        ]

        # RENDER CARDS
        for title, items in sections:
            card = tk.Frame(cols_frame, bg="white", bd=1, relief="solid")
            card.pack(side="left", fill="both", expand=True, padx=2)

            tk.Label(card, text=title, font=("Arial", 10, "bold"),
                    bg="white", fg="#7f8c8d").pack(anchor="w", padx=10, pady=(8, 2))

            for key, val in items:
                f = tk.Frame(card, bg="white")
                f.pack(fill="x", padx=10, pady=1)

                tk.Label(f, text=f"{key}:", font=("Arial", 9),
                        bg="white", fg="#2c3e50").pack(side="left")

                tk.Label(f, text=str(val), font=("Arial", 9, "bold"),
                        bg="white", fg="#1f3b63").pack(side="right")

        # FOOTER
        footer = tk.Frame(container, bg="#f0f2f5")
        footer.pack(fill="x", pady=(10, 0))

        create_button(
            footer,
            "Generate PDF Invoice",
            160,
            35,
            "#1f3b63",
            "white",
            lambda: self._download_invoice(details)
        ).pack(side="right")

        # ✅ ONLY show if unpaid or partial
        if self.user_role == "Tenant" and diff > 0:
            create_button(
                footer,
                "Pay Remaining Balance",
                180,
                35,
                "#28a745",
                "white",
                lambda: PaymentWindow(
                    self.frame.winfo_toplevel(),  # ✅ FIXED
                    self.user_id,
                    p_id,
                    diff,
                    self.refresh_payments
                )
            ).pack(side="right", padx=10)

    def _handle_filter_change(self, event, filter_type):
        val = event.widget.get()
        if filter_type == "range": self.current_range = val
        elif filter_type == "city": self.current_city = val
        elif filter_type == "late": self.current_late = val # Add this
        self._render_view()

    def _reset_filters(self):
        self.current_city = "All Cities"
        self.current_status = "All Status"
        self.current_range = "All Time"
        self.current_late = "All (Late/On-Time)" # Add this
        self.refresh_payments()

    def _set_graph_visibility(self, show):
        self.show_graphs = bool(show)
        self._update_graph_toggle_buttons()
        self._render_view()

    def _update_graph_toggle_buttons(self):
        if self.user_role != "Tenant":
            return
        if not self.show_graph_btn or not self.hide_graph_btn:
            return

        if self.show_graphs:
            self.show_graph_btn.pack_forget()
            self.hide_graph_btn.pack(side="left", padx=10)
        else:
            self.hide_graph_btn.pack_forget()
            self.show_graph_btn.pack(side="left", padx=10)

    def _chart_card(self, parent, title):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(card, text=title, bg="white", fg="#1f3b63", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=8, pady=(6, 4)
        )
        canvas = tk.Canvas(card, bg="#ffffff", width=240, height=170, highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        return canvas

    def _draw_line_chart(self, canvas, data):
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 170)
        pad = 22

        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#95a5a6")
        canvas.create_line(pad, h - pad, pad, pad, fill="#95a5a6")

        if not data:
            canvas.create_text(w / 2, h / 2, text="No data", fill="#7f8c8d")
            return

        max_y = max(v for _, v in data) or 1
        n = len(data)
        step_x = (w - (2 * pad)) / max(1, n - 1)
        points = []

        for i, (label, value) in enumerate(data):
            x = pad + i * step_x
            y = h - pad - ((value / max_y) * (h - (2 * pad)))
            points.extend([x, y])
            canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#2c7fb8", outline="#2c7fb8")
            if i % max(1, n // 4) == 0:
                canvas.create_text(x, h - 9, text=label[5:], fill="#4c5d73", font=("Arial", 8))

        if len(points) >= 4:
            canvas.create_line(*points, fill="#2c7fb8", width=2)

    def _draw_bar_chart(self, canvas, data):
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 170)
        pad = 22

        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#95a5a6")
        canvas.create_line(pad, h - pad, pad, pad, fill="#95a5a6")

        if not data:
            canvas.create_text(w / 2, h / 2, text="No late payments", fill="#7f8c8d")
            return

        max_y = max(v for _, v in data) or 1
        bar_w = (w - (2 * pad)) / max(1, len(data))
        for i, (label, value) in enumerate(data):
            x0 = pad + i * bar_w + 6
            x1 = pad + (i + 1) * bar_w - 6
            y1 = h - pad
            y0 = y1 - ((value / max_y) * (h - (2 * pad)))
            canvas.create_rectangle(x0, y0, x1, y1, fill="#e67e22", outline="#d35400")
            canvas.create_text((x0 + x1) / 2, y0 - 7, text=str(value), fill="#4c5d73", font=("Arial", 8))
            canvas.create_text((x0 + x1) / 2, h - 9, text=label, fill="#4c5d73", font=("Arial", 8))

    def _draw_compare_chart(self, canvas, tenant_avg, neighbor_avg):
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 240)
        h = max(canvas.winfo_height(), 170)
        pad = 25

        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#95a5a6")
        canvas.create_line(pad, h - pad, pad, pad, fill="#95a5a6")

        max_y = max(tenant_avg, neighbor_avg, 1)
        values = [("You", tenant_avg, "#2ecc71"), ("Neighbours", neighbor_avg, "#9b59b6")]
        bar_w = 46
        gap = 36
        start_x = (w - (2 * bar_w + gap)) / 2

        for i, (label, val, color) in enumerate(values):
            x0 = start_x + i * (bar_w + gap)
            x1 = x0 + bar_w
            y1 = h - pad
            y0 = y1 - ((val / max_y) * (h - (2 * pad)))
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)
            canvas.create_text((x0 + x1) / 2, y0 - 8, text=f"{val:.0f}", fill="#4c5d73", font=("Arial", 8, "bold"))
            canvas.create_text((x0 + x1) / 2, h - 9, text=label, fill="#4c5d73", font=("Arial", 8))

def create_page(parent, user_info):
    return PaymentsManagementPage(parent, user_info).frame
