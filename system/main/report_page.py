import tkinter as tk
from tkinter import ttk, messagebox
from database.property_service import get_all_cities
from main.helpers import create_button
from database.report_service import (
    fetch_summary_snapshot, fetch_occupancy_rows,
    fetch_financial_rows, fetch_maintenance_rows
)
from database.tenant_portal_service import (
    get_payment_history_series,
    get_late_payment_by_property,
    get_neighbor_comparison,
)
from modules.Report_Management import ReportLogicHandler

REPORT_TYPES = {
    "Occupancy": "Occupancy reports (filtered by apartment or city)",
    "Financial": "Financial summaries (collected vs pending rents)",
    "Maintenance": "Maintenance cost tracking",
}

class ReportManagementPage:
    def __init__(self, parent, user_info=None):
        self.parent, self.user_info = parent, user_info
        self.role = user_info[4] if user_info and len(user_info) > 4 else None
        self.assigned_city_id = user_info[5] if user_info and len(user_info) > 5 else None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.logic = ReportLogicHandler(self)
        self.city_name_to_id, self.available_report_types = {}, self._get_allowed_report_types()
        
        self.is_admin = self.role in ["Administrators", "Maintenance Staff"]
        self.show_report_selector = len(self.available_report_types) > 1

        self.selected_city = tk.StringVar(value="All Cities")
        default_type = self.available_report_types[0] if self.available_report_types else "Occupancy"
        self.selected_report_type = tk.StringVar(value=default_type)
        self.late_filter, self.paid_filter, self.building_filter = tk.StringVar(value="All"), tk.StringVar(value="All"), tk.StringVar(value="All Buildings")

        self.summary_cards, self.tree = {}, None
        self.current_report_title, self.current_headings, self.current_rows = "", [], []

        if self.role == "Tenant":
            self._build_tenant_dashboard_layout()
            self._render_tenant_dashboard()
            return

        self._build_layout()
        self._load_city_filter_options()
        self.generate_report()

    def _build_tenant_dashboard_layout(self):
        top_wrap = tk.Frame(self.frame, bg="#c9e4c4")
        top_wrap.pack(fill="x", padx=24, pady=(20, 8))

        tk.Label(
            top_wrap,
            text="Tenant Dashboard Analytics",
            bg="#c9e4c4",
            fg="#1f3b63",
            font=("Arial", 16, "bold"),
        ).pack(side="left")

        tk.Button(
            top_wrap,
            text="Refresh",
            command=self._render_tenant_dashboard,
            bg="#3B86FF",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=14,
            pady=6,
        ).pack(side="right")

        charts_wrap = tk.Frame(self.frame, bg="#c9e4c4")
        charts_wrap.pack(fill="both", expand=True, padx=24, pady=(4, 20))

        self.tenant_chart_payment = self._make_chart_card(
            charts_wrap,
            "Payment History Graph",
            "Shows payments over time",
        )
        self.tenant_chart_late = self._make_chart_card(
            charts_wrap,
            "Late Payment Chart",
            "How many payments were late per property",
        )
        self.tenant_chart_compare = self._make_chart_card(
            charts_wrap,
            "Comparison Graph",
            "Your payments vs close neighbours",
        )

    def _make_chart_card(self, parent, title, subtitle):
        card = tk.Frame(parent, bg="white", bd=2, relief="groove")
        card.pack(side="left", fill="both", expand=True, padx=6)

        tk.Label(card, text=title, bg="white", fg="#1f3b63", font=("Arial", 12, "bold")).pack(
            anchor="w", padx=10, pady=(10, 2)
        )
        tk.Label(card, text=subtitle, bg="white", fg="#4c5d73", font=("Arial", 9)).pack(
            anchor="w", padx=10, pady=(0, 6)
        )

        canvas = tk.Canvas(card, bg="#ffffff", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        return canvas

    def _render_tenant_dashboard(self):
        user_id = self.user_info[0] if self.user_info else None
        self._draw_line_chart(self.tenant_chart_payment, get_payment_history_series(user_id))
        self._draw_bar_chart(self.tenant_chart_late, get_late_payment_by_property(user_id))

        cmp_data = get_neighbor_comparison(user_id)
        self._draw_compare_chart(
            self.tenant_chart_compare,
            cmp_data.get("tenant_avg", 0),
            cmp_data.get("neighbor_avg", 0),
        )

    def _draw_line_chart(self, canvas, data):
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 280)
        h = max(canvas.winfo_height(), 220)
        pad = 26

        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#95a5a6")
        canvas.create_line(pad, h - pad, pad, pad, fill="#95a5a6")

        if not data:
            canvas.create_text(w / 2, h / 2, text="No payment history", fill="#7f8c8d")
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
                canvas.create_text(x, h - 10, text=label[5:], fill="#4c5d73", font=("Arial", 8))

        if len(points) >= 4:
            canvas.create_line(*points, fill="#2c7fb8", width=2)

    def _draw_bar_chart(self, canvas, data):
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 280)
        h = max(canvas.winfo_height(), 220)
        pad = 26

        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#95a5a6")
        canvas.create_line(pad, h - pad, pad, pad, fill="#95a5a6")

        if not data:
            canvas.create_text(w / 2, h / 2, text="No late payments", fill="#7f8c8d")
            return

        max_y = max(v for _, v in data) or 1
        bar_w = (w - (2 * pad)) / max(1, len(data))

        for i, (label, value) in enumerate(data):
            x0 = pad + i * bar_w + 8
            x1 = pad + (i + 1) * bar_w - 8
            y1 = h - pad
            y0 = y1 - ((value / max_y) * (h - (2 * pad)))
            canvas.create_rectangle(x0, y0, x1, y1, fill="#e67e22", outline="#d35400")
            canvas.create_text((x0 + x1) / 2, y0 - 8, text=str(value), fill="#4c5d73", font=("Arial", 8))
            canvas.create_text((x0 + x1) / 2, h - 10, text=label, fill="#4c5d73", font=("Arial", 8))

    def _draw_compare_chart(self, canvas, tenant_avg, neighbor_avg):
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 280)
        h = max(canvas.winfo_height(), 220)
        pad = 30

        canvas.create_line(pad, h - pad, w - pad, h - pad, fill="#95a5a6")
        canvas.create_line(pad, h - pad, pad, pad, fill="#95a5a6")

        max_y = max(tenant_avg, neighbor_avg, 1)
        values = [("You", tenant_avg, "#2ecc71"), ("Neighbours", neighbor_avg, "#9b59b6")]

        bar_w = 60
        gap = 50
        start_x = (w - (2 * bar_w + gap)) / 2

        for i, (label, val, color) in enumerate(values):
            x0 = start_x + i * (bar_w + gap)
            x1 = x0 + bar_w
            y1 = h - pad
            y0 = y1 - ((val / max_y) * (h - (2 * pad)))
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)
            canvas.create_text((x0 + x1) / 2, y0 - 10, text=f"{val:.0f}", fill="#4c5d73", font=("Arial", 9, "bold"))
            canvas.create_text((x0 + x1) / 2, h - 12, text=label, fill="#4c5d73", font=("Arial", 9))

    def _get_allowed_report_types(self):
        full_access = ["Occupancy", "Financial", "Maintenance"]
        permissions = {
            "Administrators": full_access,
            "Manager": full_access,
            "Maintenance Staff": full_access,
            "Finance Manager": ["Financial"]
        }
        return permissions.get(self.role, full_access)

    def _build_layout(self):
        top_wrap = tk.Frame(self.frame, bg="#c9e4c4")
        top_wrap.pack(fill="x", padx=24, pady=(20, 8))
        controls = tk.Frame(top_wrap, bg="#c9e4c4")
        controls.pack(anchor="center")

        self.city_cb = None
        if not self.is_admin:
            tk.Label(controls, text="City:", bg="#c9e4c4", fg="#1f3b63", font=("Arial", 11, "bold")).pack(side="left", padx=(0, 8))
            self.city_cb = ttk.Combobox(controls, textvariable=self.selected_city, values=["All Cities"], state="readonly", width=18, font=("Arial", 10))
            self.city_cb.pack(side="left", padx=(0, 14))
            self.city_cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        self.report_label_to_key = {}
        if self.show_report_selector:
            tk.Label(controls, text="Report:", bg="#c9e4c4", fg="#1f3b63", font=("Arial", 11, "bold")).pack(side="left", padx=(0, 8))
            report_labels = [REPORT_TYPES[r] for r in self.available_report_types]
            self.report_label_to_key = {REPORT_TYPES[key]: key for key in self.available_report_types}
            self.report_cb = ttk.Combobox(controls, values=report_labels, state="readonly", width=46, font=("Arial", 10))
            self.report_cb.pack(side="left", padx=(0, 12))
            self.report_cb.set(REPORT_TYPES[self.selected_report_type.get()])
            self.report_cb.bind("<<ComboboxSelected>>", self._on_report_type_change)

        create_button(controls, text="Generate", width=120, height=42, bg="#3B86FF", fg="white", command=self._generate_and_export).pack(side="left")

        self.financial_filter_wrap = tk.Frame(top_wrap, bg="#c9e4c4")
        for lbl, var, vals in [("Late Filter:", self.late_filter, ["All", "Late", "Not Late"]), ("Paid Filter:", self.paid_filter, ["All", "Paid", "Not Paid"])]:
            tk.Label(self.financial_filter_wrap, text=lbl, bg="#c9e4c4", fg="#1f3b63", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 6))
            cb = ttk.Combobox(self.financial_filter_wrap, textvariable=var, values=vals, state="readonly", width=10, font=("Arial", 10))
            cb.pack(side="left", padx=(0, 16))
            cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        self.maintenance_filter_wrap = tk.Frame(top_wrap, bg="#c9e4c4")
        tk.Label(self.maintenance_filter_wrap, text="Building:", bg="#c9e4c4", fg="#1f3b63", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 6))
        self.building_filter_cb = ttk.Combobox(self.maintenance_filter_wrap, textvariable=self.building_filter, values=["All Buildings"], state="readonly", width=16, font=("Arial", 10))
        self.building_filter_cb.pack(side="left", padx=(0, 16))
        self.building_filter_cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        summary_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        summary_wrap.pack(fill="x", padx=24, pady=(4, 10))
        tk.Label(summary_wrap, text="Report Snapshot", font=("Arial", 14, "bold"), bg="white", fg="#1f3b63").pack(pady=(10, 8))
        cards_row = tk.Frame(summary_wrap, bg="white")
        cards_row.pack(fill="x", padx=10, pady=(0, 10))
        
        # --- UPDATED CARD FILTERING LOGIC ---
        cards = [
            ("Apartments", "0", "#3B86FF"), 
            ("Occupancy", "0.0%", "#28a745"), 
            ("Collected", "£0.00", "#17a2b8"), 
            ("Maintenance", "£0.00", "#6c757d")
        ]
        
        if self.role == "Finance Manager": 
            cards = [c for c in cards if c[0] not in ["Occupancy", "Maintenance"]]

        elif self.role == "Maintenance Staff":
            # Hide occupancy and financial info for Maintenance Staff
            cards = [c for c in cards if c[0] not in ["Occupancy", "Collected"]]

        for idx, (label, val, col) in enumerate(cards):
            card = tk.Frame(cards_row, bg=col, bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=5, sticky="ew")
            cards_row.grid_columnconfigure(idx, weight=1)
            self.summary_cards[label] = tk.Label(card, text=val, font=("Arial", 18, "bold"), bg=col, fg="white")
            self.summary_cards[label].pack(pady=(10, 2))
            tk.Label(card, text=label, font=("Arial", 10), bg=col, fg="white").pack(pady=(0, 9))

        results_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        results_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.results_title = tk.Label(results_wrap, text="Report Results", font=("Arial", 13, "bold"), bg="white", fg="#1f3b63", anchor="w")
        self.results_title.pack(fill="x", padx=12, pady=(10, 6))
        self.table_host = tk.Frame(results_wrap, bg="white")
        self.table_host.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_city_filter_options(self):
        city_rows = get_all_cities()
        self.city_name_to_id = {name: cid for cid, name in city_rows}
        if self.role in ["Administrators", "Maintenance Staff"] and self.assigned_city_id:
            assigned = next((n for n, cid in self.city_name_to_id.items() if cid == self.assigned_city_id), None)
            if assigned: self.selected_city.set(assigned)
            return
        if self.city_cb: self.city_cb["values"] = ["All Cities"] + [n for _, n in city_rows]

    def _on_report_type_change(self, _event=None):
        key = self.report_label_to_key.get(self.report_cb.get())
        if key: self.selected_report_type.set(key)
        self.generate_report()

    def _resolve_city_id(self):
        if self.is_admin and self.assigned_city_id: return self.assigned_city_id
        name = self.city_cb.get().strip() if self.city_cb else self.selected_city.get().strip()
        return self.city_name_to_id.get(name) if name != "All Cities" else None

    def _generate_and_export(self):
        self.generate_report()
        # Wait 100ms and run export on the main loop to avoid the memory crash
        self.frame.after(100, self.logic.export_to_pdf)

    def on_show(self):
        if self.role == "Tenant":
            self._render_tenant_dashboard()
            return
        self._load_city_filter_options()
        self.generate_report()

    def generate_report(self):
        city_id = self._resolve_city_id()
        snapshot = fetch_summary_snapshot(city_id)
        
        # UPDATED: Using .get() check to avoid errors if cards are hidden
        if "Apartments" in self.summary_cards:
            self.summary_cards["Apartments"].config(text=str(snapshot["apartments"]))
        if "Occupancy" in self.summary_cards:
            self.summary_cards["Occupancy"].config(text=f"{snapshot['occupancy_rate']:.2f}%")
        if "Collected" in self.summary_cards:
            self.summary_cards["Collected"].config(text=f"£{snapshot['collected']:,.2f}")
        if "Maintenance" in self.summary_cards: 
            self.summary_cards["Maintenance"].config(text=f"£{snapshot['maintenance']:,.2f}")

        report_key, city_label = self.selected_report_type.get(), self.selected_city.get()
        self.financial_filter_wrap.pack(anchor="center", pady=(8, 2)) if report_key == "Financial" else self.financial_filter_wrap.pack_forget()
        self.maintenance_filter_wrap.pack(anchor="center", pady=(8, 2)) if report_key == "Maintenance" else self.maintenance_filter_wrap.pack_forget()

        if report_key == "Occupancy":
            rows = fetch_occupancy_rows(city_id)
            self._render_table(f"Occupancy Report - {city_label}", ("id", "city", "building", "type", "rooms", "status"),
                               ("Apartment", "City", "Building", "Type", "Rooms", "Status"), (90, 120, 230, 110, 80, 120), rows)
        elif report_key == "Financial":
            rows = fetch_financial_rows(city_id, self.late_filter.get(), self.paid_filter.get())
            self._render_table(f"Financial Summary - {city_label}", ("pid", "city", "tenant", "due", "amt", "paid", "late"),
                               ("Payment ID", "City", "Tenant", "Due Date", "Amount", "Paid", "Is Late"), (95, 110, 180, 120, 100, 85, 95), rows)
        elif report_key == "Maintenance":
            all_rows = fetch_maintenance_rows(city_id)
            self.building_filter_cb["values"] = ["All Buildings"] + sorted({str(r[2]) for r in all_rows if r[2]})
            rows = all_rows if self.building_filter.get() == "All Buildings" else [r for r in all_rows if str(r[2]) == self.building_filter.get()]
            self._render_table(f"Maintenance Cost Tracking - {city_label}", ("rid", "city", "bld", "iss", "stat", "cost", "res"),
                               ("Request ID", "City", "Building", "Issue", "Status", "Cost", "Resolved"), (90, 90, 105, 190, 115, 90, 110), rows)

    def _render_table(self, title, columns, headings, widths, rows):
        for w in self.table_host.winfo_children(): w.destroy()
        self.results_title.config(text=title)
        self.current_report_title, self.current_headings, self.current_rows = title, list(headings), rows
        if not rows: return
        tree = ttk.Treeview(self.table_host, columns=columns, show="headings", height=14)
        for col, head, wid in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=wid, anchor="center" if col in ("id", "pid", "rid", "rooms", "status") else "w")
        tree.pack(fill="both", expand=True)
        for r in rows: tree.insert("", "end", values=tuple(f"{v:.2f}" if isinstance(v, float) else v for v in r))

