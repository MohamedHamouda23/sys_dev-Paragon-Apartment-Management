import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from collections import defaultdict

from main.helpers import create_button, clear_frame, show_placeholder
from database.payment_service import get_all_payments, get_tenant_payments, get_payment_details
from database.tenant_portal_service import get_tenant_payments_with_balance, get_neighbor_comparison
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
        self.current_late = "All"
        self.show_graphs = False
        self.show_graph_btn = None
        self.hide_graph_btn = None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        try:
            self.refresh_payments()
        except Exception as exc:
            self._show_page_error(f"Payments failed to load: {exc}")

    def _show_page_error(self, message):
        clear_frame(self.content_frame)
        error_box = tk.Frame(self.content_frame, bg="white", bd=2, relief="groove")
        error_box.pack(fill="x", pady=(8, 12), padx=4)

        tk.Label(
            error_box,
            text="Payments Page Error",
            bg="white",
            fg="#c0392b",
            font=("Arial", 12, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))

        tk.Label(
            error_box,
            text=str(message),
            bg="white",
            fg="#2c3e50",
            justify="left",
            wraplength=860,
            font=("Arial", 10),
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def _normalize_status(self, status):
        """Normalize status labels to a canonical display/filter set."""
        raw = str(status or "").strip().lower()

        if raw in {"paid", "fully paid", "fully payed", "payed"}:
            return "Fully Paid"
        if raw in {"pending", "partial", "pending partial", "pending (partial)"}:
            return "Pending (Partial)"
        if raw in {"unpaid", "not paid"}:
            return "Unpaid"
        return str(status or "").strip()

    def _build_layout(self):
        # 1. Create a Canvas and a Scrollbar to handle small window sizes
        self.canvas = tk.Canvas(self.frame, bg="#c9e4c4", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        
        # 2. This inner frame will hold all the actual content
        self.scrollable_frame = tk.Frame(self.canvas, bg="#c9e4c4")
        
        # Configure the canvas to update the scroll region whenever the inner frame changes size
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create a window inside the canvas to hold our frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Make the inner frame expand to the width of the canvas
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack the canvas and scrollbar into the main self.frame
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # --- Everything below now packs into self.scrollable_frame ---

        top_bar = tk.Frame(self.scrollable_frame, bg="#c9e4c4")
        top_bar.pack(side="top", fill="x", pady=(20, 10))

        btns_inner = tk.Frame(top_bar, bg="#c9e4c4")
        btns_inner.pack(anchor="center")

        create_button(
            btns_inner,
            "Refresh",
            120,
            45,
            "#3B86FF",
            "white",
            self.refresh_payments,
        ).pack(side="left", padx=10)

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

        # Main content area (Graphs/Table)
        self.content_frame = tk.Frame(self.scrollable_frame, bg="#c9e4c4")
        self.content_frame.pack(fill="both", expand=True, padx=20)

        # Bottom "Lifecycle" box - now part of the scrollable area
        self.detail_wrap = tk.Frame(self.scrollable_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=20, pady=20)
        show_placeholder(self.detail_wrap, "Select a payment record to view the Lifecycle breakdown")

    def _download_invoice(self, details):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
        except Exception:
            messagebox.showerror(
                "PDF Error",
                "PDF export dependency is missing. Install 'reportlab' to download invoices.",
            )
            return

        p_id = details.get("payment_id", "N/A")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Invoice_{details.get('tenant_name', 'User')}_{p_id}.pdf",
            title="Save PDF Invoice",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not file_path:
            return

        try:
            pdf = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4

            pdf.setFillColor(colors.HexColor("#1f3b63"))
            pdf.rect(0, height - 80, width, 80, fill=1)
            pdf.setFillColor(colors.white)
            pdf.setFont("Helvetica-Bold", 20)
            pdf.drawString(50, height - 50, "OFFICIAL PAYMENT INVOICE")

            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, height - 120, f"Invoice Ref: #{p_id}")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, height - 135, f"Date Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")

            pdf.line(50, height - 150, width - 50, height - 150)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, height - 175, "BILL TO:")
            pdf.setFont("Helvetica", 11)
            pdf.drawString(50, height - 190, f"Tenant Name: {details.get('tenant_name', 'N/A')}")
            pdf.drawString(50, height - 205, f"Property: {details.get('property', 'N/A')}")
            pdf.drawString(50, height - 220, f"City: {details.get('city', 'N/A')}")

            pdf.setFillColor(colors.HexColor("#f0f2f5"))
            pdf.rect(50, height - 300, width - 100, 30, fill=1)
            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(60, height - 280, "Description")
            pdf.drawRightString(width - 60, height - 280, "Amount")

            pdf.setFont("Helvetica", 11)
            pdf.drawString(60, height - 320, f"Rent Payment for Due Date: {details.get('due_date', 'N/A')}")
            pdf.drawRightString(width - 60, height - 320, f"GBP {details.get('paid_amount', '0.00')}")

            pdf.line(width - 200, height - 350, width - 50, height - 350)
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(width - 200, height - 375, "TOTAL PAID:")
            pdf.drawRightString(width - 60, height - 375, f"£{details.get('paid_amount', '0.00')}")

            pdf.setFont("Helvetica-Oblique", 9)
            pdf.drawCentredString(width / 2, 50, "Thank you for your prompt payment. This is a computer-generated document.")

            pdf.save()
            messagebox.showinfo("Success", f"PDF Invoice saved successfully at:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("PDF Error", f"Failed to generate PDF: {exc}")

    def refresh_payments(self):
        try:
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
                        row.get("is_late", "No"),
                        row["lease_id"],
                        row["payment_id"],
                    )
                    for row in tenant_rows
                ]
            else:
                self._all_payments = get_tenant_payments(self.user_id) or []

            self._render_view()
        except Exception as exc:
            self._all_payments = []
            self._show_page_error(exc)

    def _safe_parse_date(self, value):
        if not value or value in ["-", "None", "N/A"]:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None

    def _row_due_date(self, row):
        return row[3] if self.user_role == "Finance Manager" else row[1]

    def _row_paid_amount(self, row):
        return float(row[5] if self.user_role == "Finance Manager" else row[3] or 0)

    def _row_agreed_amount(self, row):
        return float(row[6] if self.user_role == "Finance Manager" else row[4] or 0)

    def _row_status(self, row):
        raw_status = row[7] if self.user_role == "Finance Manager" else row[5]
        return self._normalize_status(raw_status)

    def _row_late(self, row):
        return str(row[8] if self.user_role == "Finance Manager" else row[6] or "No")

    def _row_city(self, row):
        return str(row[2] if self.user_role == "Finance Manager" else "")

    def _row_property(self, row):
        return str(row[1] if self.user_role == "Finance Manager" else row[0])

    def _row_lease_key(self, row):
        if self.user_role == "Tenant" and len(row) > 8:
            return f"Lease {row[7]}"
        return self._row_property(row)

    def _row_payment_id(self, row):
        return row[-1]

    def _matches_range(self, due_date):
        if self.current_range == "All Time":
            return True

        parsed = self._safe_parse_date(due_date)
        if not parsed:
            return False

        now = datetime.now()
        if self.current_range == "Last Month":
            return parsed >= now - timedelta(days=30)
        if self.current_range == "Last 3 Months":
            return parsed >= now - timedelta(days=90)
        return True

    def _matches_status(self, status):
        if self.current_status == "All Status":
            return True
        return self._normalize_status(status) == self._normalize_status(self.current_status)

    def _matches_late(self, late_value):
        if self.current_late == "All":
            return True
        if self.current_late == "Late Only":
            return late_value == "Yes"
        if self.current_late == "On-Time Only":
            return late_value == "No"
        return True

    def _apply_filters(self, rows):
        filtered = []
        for row in rows:
            due_date = self._row_due_date(row)
            status = self._row_status(row)
            late_value = self._row_late(row)

            if not self._matches_range(due_date):
                continue
            if not self._matches_status(status):
                continue

            if self.user_role == "Finance Manager":
                if self.current_city != "All Cities" and self._row_city(row) != self.current_city:
                    continue
                if not self._matches_late(late_value):
                    continue

            filtered.append(row)
        return filtered

    def _build_line_chart_data(self, rows):
        monthly_totals = defaultdict(float)
        for row in rows:
            due_date = self._row_due_date(row)
            parsed = self._safe_parse_date(due_date)
            if not parsed:
                continue
            monthly_totals[parsed.strftime("%Y-%m")] += self._row_paid_amount(row)
        return sorted(monthly_totals.items())

    def _build_late_chart_data(self, rows):
        late_counts = defaultdict(int)
        all_properties = set()
        for row in rows:
            property_key = self._row_property(row)
            all_properties.add(property_key)
            if self._row_late(row) == "Yes":
                late_counts[property_key] += 1

        data = [(property_key, late_counts.get(property_key, 0)) for property_key in all_properties]
        return sorted(data, key=lambda item: item[0])

    def _build_summary_chart_data(self, rows):
        total_paid = 0.0
        total_outstanding = 0.0
        for row in rows:
            paid = self._row_paid_amount(row)
            agreed = self._row_agreed_amount(row)
            total_paid += paid
            total_outstanding += max(agreed - paid, 0)
        return total_paid, total_outstanding

    def _build_neighbor_compare_data(self):
        """Return tenant-vs-neighbor payment comparison for tenant graph."""
        if self.user_role != "Tenant" or not self.user_id:
            return [("You", 0.0), ("Neighbor 1", 0.0), ("Neighbor 2", 0.0)]

        comparison = get_neighbor_comparison(self.user_id) or {}
        tenant_avg = float(comparison.get("tenant_avg") or 0)
        neighbor_1_label = str(comparison.get("neighbor_1_label") or "Neighbor 1")
        neighbor_1_avg = float(comparison.get("neighbor_1_avg") or 0)
        neighbor_2_label = str(comparison.get("neighbor_2_label") or "Neighbor 2")
        neighbor_2_avg = float(comparison.get("neighbor_2_avg") or 0)
        return [("You", tenant_avg), (neighbor_1_label, neighbor_1_avg), (neighbor_2_label, neighbor_2_avg)]

    def _render_view(self):
        clear_frame(self.content_frame)
        is_fm = self.user_role == "Finance Manager"
        filtered_rows = self._apply_filters(self._all_payments)

        f_bar = tk.Frame(self.content_frame, bg="#c9e4c4")
        f_bar.pack(fill="x", pady=(0, 10))

        tk.Label(f_bar, text="Period:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left")
        cb_r = ttk.Combobox(f_bar, values=["All Time", "Last Month", "Last 3 Months"], state="readonly", width=15)
        cb_r.set(self.current_range)
        cb_r.pack(side="left", padx=5)
        cb_r.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "range"))

        tk.Label(f_bar, text="Status:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 0))
        status_values = ["All Status", "Fully Paid", "Pending (Partial)", "Unpaid"]
        cb_s = ttk.Combobox(f_bar, values=status_values, state="readonly", width=16)
        cb_s.set(self.current_status)
        cb_s.pack(side="left", padx=5)
        cb_s.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "status"))

        if is_fm:
            tk.Label(f_bar, text="City:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 0))
            cities = ["All Cities"] + sorted({self._row_city(p) for p in self._all_payments if self._row_city(p)})
            cb_c = ttk.Combobox(f_bar, values=cities, state="readonly", width=15)
            cb_c.set(self.current_city)
            cb_c.pack(side="left", padx=5)
            cb_c.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "city"))

            tk.Label(f_bar, text="Late Status:", bg="#c9e4c4", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 0))
            cb_l = ttk.Combobox(f_bar, values=["All", "Late Only", "On-Time Only"], state="readonly", width=15)
            cb_l.set(self.current_late)
            cb_l.pack(side="left", padx=5)
            cb_l.bind("<<ComboboxSelected>>", lambda e: self._handle_filter_change(e, "late"))

        if self.user_role == "Tenant" and self.show_graphs:
            graphs_wrap = tk.Frame(self.content_frame, bg="#c9e4c4")
            graphs_wrap.pack(fill="x", expand=False, pady=(0, 10))

            graph_row = tk.Frame(graphs_wrap, bg="#c9e4c4")
            graph_row.pack(anchor="center")

            self.chart_payment = self._chart_card(
                graph_row,
                "Payment History",
                "Shows the filtered paid amount over time",
            )
            self.chart_late = self._chart_card(
                graph_row,
                "Late Payments Per Apartment",
                "Y-axis: late count, X-axis: apartment",
            )
            self.chart_summary = self._chart_card(
                graph_row,
                "You vs Nearby Tenants",
                "Average paid amount per payment",
            )

            self._draw_line_chart(self.chart_payment, self._build_line_chart_data(filtered_rows))
            self._draw_late_lease_bar_chart(self.chart_late, self._build_late_chart_data(filtered_rows))
            compare_items = self._build_neighbor_compare_data()
            self._draw_compare_chart(self.chart_summary, compare_items)

        cols = (
            ("tenant", "unit", "city", "due", "paid_dt", "paid_amt", "agreed", "stat", "late")
            if is_fm
            else ("unit", "due", "paid_dt", "paid_amt", "agreed", "stat", "late")
        )
        heads = (
            ("Tenant", "Unit", "City", "Due Date", "Paid Date", "Paid", "Agreed", "Status", "Late")
            if is_fm
            else ("Unit", "Due Date", "Paid Date", "Paid", "Agreed", "Status", "Late")
        )
        widths = (
            (120, 140, 100, 100, 100, 80, 80, 120, 60)
            if is_fm
            else (220, 110, 110, 90, 90, 130, 70)
        )

        table_wrap = tk.Frame(self.content_frame, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, pady=(0, 12))
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", height=12)
        for col, heading, width in zip(cols, heads, widths):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="center")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        y_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=(8, 0))
        x_scroll.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_row_select())
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for row in filtered_rows:
            payment_id = self._row_payment_id(row)
            display_values = list(row[: len(cols)])
            status_col_idx = 7 if is_fm else 5
            if len(display_values) > status_col_idx:
                display_values[status_col_idx] = self._normalize_status(display_values[status_col_idx])
            self.tree.insert("", "end", values=display_values, tags=(payment_id,))

    def _on_row_select(self):
        selection = self.tree.selection()
        if not selection:
            return
        payment_id = self.tree.item(selection[0])["tags"][0]
        details = get_payment_details(payment_id)
        if not details:
            return
        self._render_lifecycle_detail_panel(payment_id, details)

    def _render_lifecycle_detail_panel(self, payment_id, details):
        clear_frame(self.detail_wrap)

        container = tk.Frame(self.detail_wrap, bg="#f0f2f5")
        container.pack(fill="both", expand=True, padx=15, pady=(10, 10))

        header = tk.Frame(container, bg="white", bd=1, relief="solid")
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text=f"TRANSACTION MANAGEMENT: #{payment_id}",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#1f3b63",
        ).pack(side="left", padx=12, pady=8)

        agreed = float(details.get("agreed_rent", 0) or 0)
        payment_date = details.get("payment_date")
        raw_paid = float(details.get("paid_amount", 0) or 0)
        paid = 0.0 if not payment_date or payment_date in ["-", "None", "N/A"] else raw_paid
        outstanding = max(agreed - paid, 0)

        if paid == 0:
            status_text, badge_bg = "UNPAID", "#e74c3c"
        elif paid < agreed:
            status_text, badge_bg = "PARTIAL", "#f39c12"
        else:
            status_text, badge_bg = "PAID", "#27ae60"

        tk.Label(
            header,
            text=status_text,
            bg=badge_bg,
            fg="white",
            font=("Arial", 8, "bold"),
            padx=10,
            pady=2,
        ).pack(side="right", padx=12)

        cols_frame = tk.Frame(container, bg="#f0f2f5")
        cols_frame.pack(fill="x")

        sections = [
            ("Occupant Info", [
                ("Tenant", details.get("tenant_name")),
                ("Property", details.get("property")),
                ("Location", details.get("city", "N/A")),
            ]),
            ("Billing Period", [
                ("Due Date", details.get("due_date")),
                ("Paid Date", payment_date if payment_date else "-"),
                ("Late status", details.get("is_late", "No")),
            ]),
            ("Financial Breakdown", [
                ("Expected", f"£{agreed:.2f}"),
                ("Actual Paid", f"£{paid:.2f}"),
                ("Outstanding", f"£{outstanding:.2f}"),
            ]),
        ]

        for title, items in sections:
            card = tk.Frame(cols_frame, bg="white", bd=1, relief="solid")
            card.pack(side="left", fill="both", expand=True, padx=2)

            tk.Label(
                card,
                text=title,
                font=("Arial", 9, "bold"),
                bg="white",
                fg="#7f8c8d"
            ).pack(anchor="w", padx=8, pady=(6, 3))

            for key, value in items:
                row_frame = tk.Frame(card, bg="white")
                row_frame.pack(fill="x", padx=8, pady=1)

                tk.Label(
                    row_frame,
                    text=f"{key}:",
                    font=("Arial", 8),
                    bg="white",
                    fg="#2c3e50"
                ).pack(side="left")

                tk.Label(
                    row_frame,
                    text=str(value),
                    font=("Arial", 8, "bold"),
                    bg="white",
                    fg="#1f3b63"
                ).pack(side="right")

        footer = tk.Frame(container, bg="#f0f2f5")
        footer.pack(fill="x", pady=(10, 0))

        button_wrap = tk.Frame(footer, bg="#f0f2f5")
        button_wrap.pack(anchor="center")

        create_button(
            button_wrap,
            "Download PDF Invoice",
            240,
            42,
            "#2d6cdf",
            "white",
            lambda: self._download_invoice(details),
        ).pack(side="left", padx=6)

        if self.user_role == "Tenant" and outstanding > 0:
            create_button(
                button_wrap,
                "Pay Now",
                170,
                36,
                "#28a745",
                "white",
                lambda: PaymentWindow(
                    self.frame.winfo_toplevel(),
                    self.user_id,
                    payment_id,
                    outstanding,
                    self.refresh_payments,
                ),
            ).pack(side="left", padx=6)
        
    def _handle_filter_change(self, event, filter_type):
        value = event.widget.get()
        if filter_type == "range":
            self.current_range = value
        elif filter_type == "city":
            self.current_city = value
        elif filter_type == "late":
            self.current_late = value
        elif filter_type == "status":
            self.current_status = value
        self._render_view()

    def _reset_filters(self):
        self.current_city = "All Cities"
        self.current_status = "All Status"
        self.current_range = "All Time"
        self.current_late = "All"
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

    def _chart_card(self, parent, title, subtitle):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid", width=300, height=250)
        card.pack(side="left", padx=6)
        card.pack_propagate(False)

        tk.Label(card, text=title, bg="white", fg="#1f3b63", font=("Arial", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        tk.Label(card, text=subtitle, bg="white", fg="#5d6d7e", font=("Arial", 8)).pack(anchor="w", padx=8, pady=(0, 4))

        canvas = tk.Canvas(card, bg="#ffffff", width=280, height=180, highlightthickness=0)
        canvas.pack(fill="none", expand=False, padx=8, pady=(0, 8))
        return canvas

    def _redraw_tenant_charts(self, filtered_rows, compare_items):
        if self.user_role != "Tenant" or not self.show_graphs:
            return
        if not all(hasattr(self, name) for name in ("chart_payment", "chart_late", "chart_summary")):
            return

        self._draw_line_chart(self.chart_payment, self._build_line_chart_data(filtered_rows))
        self._draw_late_lease_bar_chart(self.chart_late, self._build_late_chart_data(filtered_rows))
        self._draw_compare_chart(self.chart_summary, compare_items)

    def _draw_line_chart(self, canvas, data):
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), int(float(canvas.cget("width"))), 260)
        height = max(canvas.winfo_height(), int(float(canvas.cget("height"))), 180)
        pad = 28

        plot_w = min(width - (2 * pad), 340)
        x0 = (width - plot_w) / 2
        x1 = x0 + plot_w

        canvas.create_rectangle(0, 0, width, height, fill="#ffffff", outline="")
        canvas.create_line(x0, height - pad, x1, height - pad, fill="#b0b8c1", width=2)
        canvas.create_line(x0, height - pad, x0, pad, fill="#b0b8c1", width=2)

        if not data:
            canvas.create_text(width / 2, height / 2, text="No payment data", fill="#7f8c8d", font=("Arial", 10, "bold"))
            return

        max_y = max(value for _, value in data) or 1
        step_x = plot_w / max(1, len(data) - 1)
        points = []

        for i, (label, value) in enumerate(data):
            x = x0 + (i * step_x)
            y = height - pad - ((value / max_y) * (height - (2 * pad)))
            points.extend([x, y])
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#2c7fb8", outline="#2c7fb8")
            canvas.create_text(x, height - 12, text=label[5:], fill="#4c5d73", font=("Arial", 8))

        if len(points) >= 4:
            canvas.create_line(*points, fill="#2c7fb8", width=3, smooth=True)

    def _draw_late_lease_bar_chart(self, canvas, data):
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), int(float(canvas.cget("width"))), 260)
        height = max(canvas.winfo_height(), int(float(canvas.cget("height"))), 180)
        pad = 28

        plot_w = min(width - (2 * pad), 340)
        x0 = (width - plot_w) / 2
        x1 = x0 + plot_w

        canvas.create_rectangle(0, 0, width, height, fill="#ffffff", outline="")
        canvas.create_line(x0, height - pad, x1, height - pad, fill="#b0b8c1", width=2)
        canvas.create_line(x0, height - pad, x0, pad, fill="#b0b8c1", width=2)

        if not data:
            canvas.create_text(width / 2, height / 2, text="No late payments", fill="#7f8c8d", font=("Arial", 10, "bold"))
            return

        display_data = data[:8]
        max_y = max(value for _, value in display_data) or 1
        slot_width = plot_w / max(1, len(display_data))
        palette = ["#e67e22", "#3498db", "#9b59b6", "#2ecc71", "#e74c3c", "#f1c40f", "#1abc9c", "#34495e"]

        for i, (label, value) in enumerate(display_data):
            bar_x0 = x0 + (i * slot_width) + 8
            bar_x1 = x0 + ((i + 1) * slot_width) - 8
            y1 = height - pad
            y0 = y1 - ((value / max_y) * (height - (2 * pad)))
            color = palette[i % len(palette)]

            canvas.create_rectangle(bar_x0, y0, bar_x1, y1, fill=color, outline=color, width=1)
            canvas.create_text((bar_x0 + bar_x1) / 2, y0 - 10, text=str(value), fill="#4c5d73", font=("Arial", 8, "bold"))
            short_label = label if len(label) <= 14 else f"{label[:12]}.."
            canvas.create_text((bar_x0 + bar_x1) / 2, height - 12, text=short_label, fill="#4c5d73", font=("Arial", 7))

    def _draw_compare_chart(self, canvas, items):
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), int(float(canvas.cget("width"))), 260)
        height = max(canvas.winfo_height(), int(float(canvas.cget("height"))), 180)
        pad = 30

        canvas.create_rectangle(0, 0, width, height, fill="#ffffff", outline="")
        plot_w = min(width - (2 * pad), 340)
        x0 = (width - plot_w) / 2
        x1 = x0 + plot_w
        canvas.create_line(x0, height - pad, x1, height - pad, fill="#b0b8c1", width=2)
        canvas.create_line(x0, height - pad, x0, pad, fill="#b0b8c1", width=2)

        values = list(items) if items else [("You", 0.0), ("Neighbor 1", 0.0), ("Neighbor 2", 0.0)]
        max_y = max([v for _, v in values] + [1])
        palette = ["#2ecc71", "#9b59b6", "#3498db", "#f39c12"]
        slot_width = plot_w / max(1, len(values))

        for i, (label, value) in enumerate(values):
            color = palette[i % len(palette)]
            bar_x0 = x0 + (i * slot_width) + 10
            bar_x1 = x0 + ((i + 1) * slot_width) - 10
            y1 = height - pad
            y0 = y1 - ((value / max_y) * (height - (2 * pad)))
            canvas.create_rectangle(bar_x0, y0, bar_x1, y1, fill=color, outline=color)
            canvas.create_text((bar_x0 + bar_x1) / 2, y0 - 10, text=f"£{value:.0f}", fill="#4c5d73", font=("Arial", 8, "bold"))
            short_label = label if len(label) <= 12 else f"{label[:10]}.."
            canvas.create_text((bar_x0 + bar_x1) / 2, height - 12, text=short_label, fill="#4c5d73", font=("Arial", 8))


def create_page(parent, user_info):
    return PaymentsManagementPage(parent, user_info).frame
