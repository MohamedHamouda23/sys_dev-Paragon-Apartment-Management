
import os
import importlib
import textwrap
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from database.databaseConnection import check_connection
from database.property_service import get_all_cities
from main.helpers import create_button


REPORT_TYPES = {
    "Occupancy": "Occupancy reports (filtered by apartment or city)",
    "Financial": "Financial summaries (collected vs pending rents)",
    "Maintenance": "Maintenance cost tracking",
}


class ReportManagementPage:
    """Report dashboard with role-based access and city filtering."""

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info
        self.role = user_info[4] if user_info and len(user_info) > 4 else None
        self.assigned_city_id = user_info[5] if user_info and len(user_info) > 5 else None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.city_name_to_id = {}
        self.available_report_types = self._get_allowed_report_types()
        self.is_admin = self.role == "Administrators"
        self.show_report_selector = len(self.available_report_types) > 1

        self.selected_city = tk.StringVar(value="All Cities")
        default_type = self.available_report_types[0] if self.available_report_types else "Occupancy"
        self.selected_report_type = tk.StringVar(value=default_type)
        self.late_filter = tk.StringVar(value="All")
        self.paid_filter = tk.StringVar(value="All")
        self.building_filter = tk.StringVar(value="All Buildings")

        self.summary_cards = {}
        self.tree = None
        self.current_report_title = ""
        self.current_headings = []
        self.current_rows = []

        self._build_layout()
        self._load_city_filter_options()
        self.generate_report()

    def _get_allowed_report_types(self):
        role_map = {
            "Administrators": ["Occupancy", "Financial", "Maintenance"],
            "Manager": ["Occupancy", "Financial", "Maintenance"],
            "Finance Manager": ["Financial"],
            "Maintenance Staff": ["Maintenance"],
        }
        return role_map.get(self.role, ["Occupancy", "Financial", "Maintenance"])

    def _build_layout(self):
        top_wrap = tk.Frame(self.frame, bg="#c9e4c4")
        top_wrap.pack(fill="x", padx=24, pady=(20, 8))

        controls = tk.Frame(top_wrap, bg="#c9e4c4")
        controls.pack(anchor="center")

        self.city_cb = None
        if not self.is_admin:
            tk.Label(
                controls,
                text="City:",
                bg="#c9e4c4",
                fg="#1f3b63",
                font=("Arial", 11, "bold"),
            ).pack(side="left", padx=(0, 8))

            self.city_cb = ttk.Combobox(
                controls,
                textvariable=self.selected_city,
                values=["All Cities"],
                state="readonly",
                width=18,
                font=("Arial", 10),
            )
            self.city_cb.pack(side="left", padx=(0, 14))
            self.city_cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        self.report_cb = None
        self.report_label_to_key = {}
        if self.show_report_selector:
            tk.Label(
                controls,
                text="Report:",
                bg="#c9e4c4",
                fg="#1f3b63",
                font=("Arial", 11, "bold"),
            ).pack(side="left", padx=(0, 8))

            report_labels = [REPORT_TYPES[r] for r in self.available_report_types]
            self.report_label_to_key = {REPORT_TYPES[key]: key for key in self.available_report_types}

            self.report_cb = ttk.Combobox(
                controls,
                values=report_labels,
                state="readonly",
                width=46,
                font=("Arial", 10),
            )
            self.report_cb.pack(side="left", padx=(0, 12))
            self.report_cb.set(REPORT_TYPES[self.selected_report_type.get()])
            self.report_cb.bind("<<ComboboxSelected>>", self._on_report_type_change)

        create_button(
            controls,
            text="Generate",
            width=120,
            height=42,
            bg="#3B86FF",
            fg="white",
            command=self._generate_and_export,
        ).pack(side="left")

        self.financial_filter_wrap = tk.Frame(top_wrap, bg="#c9e4c4")

        tk.Label(
            self.financial_filter_wrap,
            text="Late Filter:",
            bg="#c9e4c4",
            fg="#1f3b63",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        self.late_filter_cb = ttk.Combobox(
            self.financial_filter_wrap,
            textvariable=self.late_filter,
            values=["All", "Late", "Not Late"],
            state="readonly",
            width=10,
            font=("Arial", 10),
        )
        self.late_filter_cb.pack(side="left", padx=(0, 16))
        self.late_filter_cb.current(0)
        self.late_filter_cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        tk.Label(
            self.financial_filter_wrap,
            text="Paid Filter:",
            bg="#c9e4c4",
            fg="#1f3b63",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        self.paid_filter_cb = ttk.Combobox(
            self.financial_filter_wrap,
            textvariable=self.paid_filter,
            values=["All", "Paid", "Not Paid"],
            state="readonly",
            width=10,
            font=("Arial", 10),
        )
        self.paid_filter_cb.pack(side="left", padx=(0, 16))
        self.paid_filter_cb.current(0)
        self.paid_filter_cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        self.maintenance_filter_wrap = tk.Frame(top_wrap, bg="#c9e4c4")

        tk.Label(
            self.maintenance_filter_wrap,
            text="Building:",
            bg="#c9e4c4",
            fg="#1f3b63",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(0, 6))

        self.building_filter_cb = ttk.Combobox(
            self.maintenance_filter_wrap,
            textvariable=self.building_filter,
            values=["All Buildings"],
            state="readonly",
            width=16,
            font=("Arial", 10),
        )
        self.building_filter_cb.pack(side="left", padx=(0, 16))
        self.building_filter_cb.current(0)
        self.building_filter_cb.bind("<<ComboboxSelected>>", lambda _e: self.generate_report())

        summary_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        summary_wrap.pack(fill="x", padx=24, pady=(4, 10))

        tk.Label(
            summary_wrap,
            text="Report Snapshot",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#1f3b63",
        ).pack(pady=(10, 8))

        cards_row = tk.Frame(summary_wrap, bg="white")
        cards_row.pack(fill="x", padx=10, pady=(0, 10))

        cards = [
            ("Apartments", "0", "#3B86FF"),
            ("Occupancy", "0.0%", "#28a745"),
            ("Collected", "£0.00", "#17a2b8"),
            ("Maintenance", "£0.00", "#6c757d"),
        ]
        if self.role == "Finance Manager":
            cards = [card for card in cards if card[0] != "Maintenance"]

        for idx, (label, value, color) in enumerate(cards):
            card = tk.Frame(cards_row, bg=color, bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=5, sticky="ew")
            cards_row.grid_columnconfigure(idx, weight=1)

            value_lbl = tk.Label(
                card,
                text=value,
                font=("Arial", 18, "bold"),
                bg=color,
                fg="white",
            )
            value_lbl.pack(pady=(10, 2))

            tk.Label(
                card,
                text=label,
                font=("Arial", 10),
                bg=color,
                fg="white",
            ).pack(pady=(0, 9))

            self.summary_cards[label] = value_lbl

        results_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        results_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.results_title = tk.Label(
            results_wrap,
            text="Report Results",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#1f3b63",
            anchor="w",
        )
        self.results_title.pack(fill="x", padx=12, pady=(10, 6))

        self.table_host = tk.Frame(results_wrap, bg="white")
        self.table_host.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_city_filter_options(self):
        city_rows = get_all_cities()
        self.city_name_to_id = {name: city_id for city_id, name in city_rows}
        city_names = [name for _, name in city_rows]

        if self.role == "Administrators" and self.assigned_city_id:
            assigned_name = next((name for name, cid in self.city_name_to_id.items() if cid == self.assigned_city_id), None)
            if assigned_name:
                self.selected_city.set(assigned_name)
                return

        if self.city_cb:
            self.city_cb["values"] = ["All Cities"] + city_names
            if self.selected_city.get() not in self.city_cb["values"]:
                self.selected_city.set("All Cities")

    def _on_report_type_change(self, _event=None):
        if not self.report_cb:
            return
        selected_label = self.report_cb.get()
        selected_key = self.report_label_to_key.get(selected_label)
        if selected_key:
            self.selected_report_type.set(selected_key)
        self.generate_report()

    def _resolve_city_id(self):
        if self.is_admin and self.assigned_city_id:
            return self.assigned_city_id

        city_name = self.city_cb.get().strip() if self.city_cb else self.selected_city.get().strip()
        if city_name == "All Cities":
            return None
        return self.city_name_to_id.get(city_name)

    def _query(self, sql, params=()):
        conn = check_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _fetch_summary_snapshot(self, city_id=None):
        where = ""
        params = ()
        if city_id is not None:
            where = " WHERE a.city_id = ?"
            params = (city_id,)

        apartment_stats = self._query(
            f"""
            SELECT
                COUNT(*) AS total_apartments,
                SUM(CASE WHEN a.occupancy_status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_apartments
            FROM Apartments a
            {where}
            """,
            params,
        )
        total_apartments, occupied_apartments = apartment_stats[0]
        total_apartments = total_apartments or 0
        occupied_apartments = occupied_apartments or 0

        financial_where = ""
        financial_params = ()
        if city_id is not None:
            financial_where = " WHERE a.city_id = ?"
            financial_params = (city_id,)

        finance_stats = self._query(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN p.payment_date IS NOT NULL THEN p.amount ELSE 0 END), 0) AS collected,
                COALESCE(SUM(CASE WHEN p.payment_date IS NULL THEN p.amount ELSE 0 END), 0) AS pending
            FROM Payment p
            JOIN Lease l ON p.lease_id = l.lease_id
            JOIN Apartments a ON l.apartment_id = a.apartment_id
            {financial_where}
            """,
            financial_params,
        )
        collected, pending = finance_stats[0]

        maintenance_where = ""
        maintenance_params = ()
        if city_id is not None:
            maintenance_where = " WHERE a.city_id = ?"
            maintenance_params = (city_id,)

        maintenance_cost = self._query(
            f"""
            SELECT COALESCE(SUM(mr.repair_cost), 0)
            FROM Maintenance_Request mr
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            {maintenance_where}
            """,
            maintenance_params,
        )[0][0]

        occupancy_rate = round((occupied_apartments / total_apartments) * 100, 2) if total_apartments else 0.0

        return {
            "apartments": total_apartments,
            "occupancy_rate": occupancy_rate,
            "collected": float(collected or 0),
            "pending": float(pending or 0),
            "maintenance": float(maintenance_cost or 0),
        }

    def _fetch_occupancy_rows(self, city_id=None):
        sql = """
            SELECT
                a.apartment_id,
                l.city_name,
                b.street || ' (' || b.postcode || ')' AS building,
                a.type,
                a.num_rooms,
                a.occupancy_status
            FROM Apartments a
            JOIN Location l ON a.city_id = l.city_id
            JOIN Buildings b ON a.building_id = b.building_id
        """
        params = ()
        if city_id is not None:
            sql += " WHERE a.city_id = ?"
            params = (city_id,)
        sql += " ORDER BY l.city_name, a.apartment_id"
        return self._query(sql, params)

    def _fetch_financial_rows(self, city_id=None, late_filter="All", paid_filter="All"):
        late_filter = (late_filter or "All").strip().lower()
        paid_filter = (paid_filter or "All").strip().lower()

        sql = """
            SELECT
                p.payment_id,
                l2.city_name,
                u.first_name || ' ' || u.surname AS tenant_name,
                DATE(p.due_date) AS due_date,
                ROUND(p.amount, 2) AS amount,
                CASE
                    WHEN p.payment_date IS NOT NULL THEN 'Yes'
                    ELSE 'No'
                END AS is_paid,
                CASE
                    WHEN COALESCE(p.Is_late, 0) = 1 THEN 'Yes'
                    ELSE 'No'
                END AS is_late
            FROM Payment p
            JOIN Lease l ON p.lease_id = l.lease_id
            JOIN Tenant t ON l.tenant_id = t.tenant_id
            JOIN User u ON t.user_id = u.user_id
            JOIN Apartments a ON l.apartment_id = a.apartment_id
            JOIN Location l2 ON a.city_id = l2.city_id
        """
        where_clauses = []
        params = []
        if city_id is not None:
            where_clauses.append("a.city_id = ?")
            params.append(city_id)

        if paid_filter == "paid":
            where_clauses.append("p.payment_date IS NOT NULL")
        elif paid_filter == "not paid":
            where_clauses.append("p.payment_date IS NULL")

        if late_filter == "late":
            where_clauses.append("COALESCE(p.Is_late, 0) = 1")
        elif late_filter == "not late":
            where_clauses.append("COALESCE(p.Is_late, 0) = 0")

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += " ORDER BY p.due_date DESC, p.payment_id DESC"
        return self._query(sql, tuple(params))

    def _toggle_financial_filters(self, visible):
        if visible:
            self.financial_filter_wrap.pack(anchor="center", pady=(8, 2))
            return

        self.financial_filter_wrap.pack_forget()
        self.late_filter.set("All")
        self.paid_filter.set("All")

    def _toggle_maintenance_filters(self, visible):
        if visible:
            self.maintenance_filter_wrap.pack(anchor="center", pady=(8, 2))
            return

        self.maintenance_filter_wrap.pack_forget()
        self.building_filter.set("All Buildings")

    def _load_building_filter_options(self, maintenance_rows):
        # Maintenance query row shape: (request_id, city, building_postcode, issue, status, cost, resolved)
        buildings = sorted({str(row[2]).strip() for row in maintenance_rows if len(row) > 2 and row[2] not in (None, "")})
        options = ["All Buildings"] + buildings
        self.building_filter_cb["values"] = options

        current = (self.building_filter_cb.get() or "All Buildings").strip()
        if current not in options:
            current = "All Buildings"
        self.building_filter_cb.set(current)

    def _get_financial_filter_values(self):
        late_value = self.late_filter_cb.get().strip() if hasattr(self, "late_filter_cb") else self.late_filter.get().strip()
        paid_value = self.paid_filter_cb.get().strip() if hasattr(self, "paid_filter_cb") else self.paid_filter.get().strip()
        return late_value or "All", paid_value or "All"

    def _fetch_maintenance_rows(self, city_id=None):
        sql = """
            SELECT
                mr.request_id,
                l.city_name,
                b.postcode AS building,
                mr.issue,
                mr.Maintenance_status,
                COALESCE(ROUND(mr.repair_cost, 2), 0) AS repair_cost,
                COALESCE(DATE(mr.resolved_date), '-') AS resolved_date
            FROM Maintenance_Request mr
            JOIN Apartments a ON mr.apartment_id = a.apartment_id
            JOIN Buildings b ON a.building_id = b.building_id
            JOIN Location l ON a.city_id = l.city_id
        """
        params = ()
        if city_id is not None:
            sql += " WHERE a.city_id = ?"
            params = (city_id,)
        sql += " ORDER BY mr.request_id DESC"
        return self._query(sql, params)

    def _render_table(self, title, columns, headings, widths, rows):
        for widget in self.table_host.winfo_children():
            widget.destroy()

        self.results_title.configure(text=title)

        self.current_report_title = title
        self.current_headings = list(headings)
        self.current_rows = rows

        if not rows:
            empty_wrap = tk.Frame(self.table_host, bg="white")
            empty_wrap.pack(fill="both", expand=True)

            empty_box = tk.Frame(empty_wrap, bg="white")
            empty_box.place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(
                empty_box,
                text="No data found for selected filter",
                font=("Arial", 14, "bold"),
                bg="white",
                fg="#2f4f6f",
            ).pack()
            tk.Label(
                empty_box,
                text="Try another city or report type.",
                font=("Arial", 10),
                bg="white",
                fg="#6f7f92",
            ).pack(pady=(6, 0))
            self.tree = None
            return

        table_container = tk.Frame(self.table_host, bg="white")
        table_container.pack(fill="both", expand=True)

        tree = ttk.Treeview(table_container, columns=columns, show="headings", height=14)
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for col, heading, width in zip(columns, headings, widths):
            tree.heading(col, text=heading)
            anchor = "center" if col in ("id", "payment_id", "request_id", "rooms", "status") else "w"
            tree.column(col, width=width, anchor=anchor)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        for row in rows:
            normalized = list(row)
            for i, value in enumerate(normalized):
                if isinstance(value, float):
                    normalized[i] = f"{value:.2f}"
            tree.insert("", "end", values=tuple(normalized))

        self.tree = tree

    def _export_current_report_to_pdf(self):
        if not self.current_headings:
            messagebox.showwarning("Export PDF", "Generate a report before exporting.")
            return

        try:
            pagesizes_module = importlib.import_module("reportlab.lib.pagesizes")
            pdfgen_canvas_module = importlib.import_module("reportlab.pdfgen.canvas")
            A4 = pagesizes_module.A4
            Canvas = pdfgen_canvas_module.Canvas
        except ImportError:
            messagebox.showerror(
                "Export PDF",
                "PDF export requires reportlab. Install it with: pip install reportlab",
            )
            return

        safe_title = self.current_report_title.replace(" ", "_").replace("-", "_")
        default_name = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = filedialog.asksaveasfilename(
            title="Save Report PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not output_path:
            return

        pdf = Canvas(output_path, pagesize=A4)
        page_w, page_h = A4
        left_margin = 34
        right_margin = 34
        top_margin = 34
        bottom_margin = 34
        line_h = 12
        table_width = page_w - left_margin - right_margin
        page_number = 1

        def draw_footer(page_no):
            pdf.setStrokeColorRGB(0.82, 0.84, 0.88)
            pdf.setLineWidth(0.7)
            pdf.line(left_margin, bottom_margin + 9, page_w - right_margin, bottom_margin + 9)
            pdf.setFont("Helvetica", 8)
            pdf.setFillColorRGB(0.35, 0.39, 0.45)
            pdf.drawString(left_margin, bottom_margin - 2, "Paragon Apartments")
            pdf.drawRightString(page_w - right_margin, bottom_margin - 2, f"Page {page_no}")

        def draw_header():
            y_top = page_h - top_margin

            pdf.setFillColorRGB(0.16, 0.41, 0.76)
            pdf.roundRect(left_margin, y_top - 28, table_width, 24, 4, stroke=0, fill=1)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(left_margin + 8, y_top - 21, "Paragon Apartments - Official Report")

            pdf.setFillColorRGB(0.17, 0.2, 0.25)
            pdf.setFont("Helvetica", 9)
            pdf.drawRightString(
                page_w - right_margin - 8,
                y_top - 21,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            )

            report_y = y_top - 44
            pdf.setFont("Helvetica-Bold", 11)
            pdf.setFillColorRGB(0.12, 0.23, 0.39)
            pdf.drawString(left_margin, report_y, self.current_report_title)

            summary_labels = list(self.summary_cards.keys())
            summary_values = [self.summary_cards[label].cget("text") for label in summary_labels]

            box_gap = 8
            box_count = max(1, len(summary_labels))
            box_w = (table_width - (box_gap * (box_count - 1))) / box_count
            box_h = 34
            box_y = report_y - 44

            for idx, (label, value) in enumerate(zip(summary_labels, summary_values)):
                x = left_margin + idx * (box_w + box_gap)
                pdf.setFillColorRGB(0.95, 0.97, 1)
                pdf.setStrokeColorRGB(0.74, 0.8, 0.9)
                pdf.roundRect(x, box_y, box_w, box_h, 3, stroke=1, fill=1)

                pdf.setFont("Helvetica-Bold", 8)
                pdf.setFillColorRGB(0.24, 0.32, 0.46)
                pdf.drawString(x + 6, box_y + 22, label)

                pdf.setFont("Helvetica-Bold", 10)
                pdf.setFillColorRGB(0.1, 0.19, 0.33)
                pdf.drawString(x + 6, box_y + 9, str(value))

            return box_y - 14

        def draw_table_header(y_top, column_widths):
            header_h = 18
            pdf.setFillColorRGB(0.2, 0.42, 0.77)
            pdf.rect(left_margin, y_top - header_h, table_width, header_h, fill=1, stroke=0)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 8)

            x = left_margin
            for i, heading in enumerate(self.current_headings):
                pdf.drawString(x + 4, y_top - 12, str(heading))
                x += column_widths[i]

            pdf.setStrokeColorRGB(0.82, 0.86, 0.92)
            x = left_margin
            for w in column_widths:
                pdf.line(x, y_top - header_h, x, y_top)
                x += w
            pdf.line(left_margin + table_width, y_top - header_h, left_margin + table_width, y_top)
            pdf.line(left_margin, y_top - header_h, left_margin + table_width, y_top - header_h)
            return y_top - header_h

        def normalize_row(row):
            values = []
            for val in row:
                text = "" if val is None else str(val)
                values.append(text)
            while len(values) < len(self.current_headings):
                values.append("")
            return values[: len(self.current_headings)]

        content_top = draw_header()
        col_count = max(1, len(self.current_headings))

        raw_weights = []
        for idx, heading in enumerate(self.current_headings):
            max_len = len(str(heading))
            for row in self.current_rows:
                row_vals = normalize_row(row)
                max_len = max(max_len, len(row_vals[idx]))
            raw_weights.append(max(8, min(36, max_len)))

        total_weight = sum(raw_weights) if raw_weights else 1
        column_widths = [(w / total_weight) * table_width for w in raw_weights] if raw_weights else [table_width]

        y = draw_table_header(content_top, column_widths)

        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.14, 0.16, 0.2)

        for row in self.current_rows:
            cells = normalize_row(row)
            wrapped_cells = []
            max_lines = 1

            for i, cell in enumerate(cells):
                approx_chars = max(6, int(column_widths[i] / 4.6))
                wrapped = textwrap.wrap(cell, width=approx_chars) or [""]
                wrapped = wrapped[:3]
                wrapped_cells.append(wrapped)
                max_lines = max(max_lines, len(wrapped))

            row_height = (max_lines * line_h) + 6
            if y - row_height < bottom_margin + 18:
                draw_footer(page_number)
                pdf.showPage()
                page_number += 1
                content_top = draw_header()
                y = draw_table_header(content_top, column_widths)
                pdf.setFont("Helvetica", 8)
                pdf.setFillColorRGB(0.14, 0.16, 0.2)

            pdf.setStrokeColorRGB(0.86, 0.89, 0.94)
            pdf.rect(left_margin, y - row_height, table_width, row_height, fill=0, stroke=1)

            x = left_margin
            for i, lines in enumerate(wrapped_cells):
                if i > 0:
                    pdf.line(x, y - row_height, x, y)

                text_y = y - 10
                for line in lines:
                    pdf.drawString(x + 3, text_y, line)
                    text_y -= line_h

                x += column_widths[i]

            y -= row_height

        draw_footer(page_number)
        pdf.save()
        messagebox.showinfo("Export PDF", f"Report saved:\n{os.path.abspath(output_path)}")

    def _generate_and_export(self):
        self.generate_report()
        self._export_current_report_to_pdf()

    def on_show(self):
        """Refresh report data when the page is brought to front."""
        self._load_city_filter_options()
        self.generate_report()

    def generate_report(self):
        city_id = self._resolve_city_id()
        snapshot = self._fetch_summary_snapshot(city_id=city_id)

        self.summary_cards["Apartments"].configure(text=str(snapshot["apartments"]))
        self.summary_cards["Occupancy"].configure(text=f"{snapshot['occupancy_rate']:.2f}%")
        self.summary_cards["Collected"].configure(text=f"£{snapshot['collected']:,.2f}")
        if "Maintenance" in self.summary_cards:
            self.summary_cards["Maintenance"].configure(text=f"£{snapshot['maintenance']:,.2f}")

        report_key = self.selected_report_type.get()
        city_name = self.selected_city.get() if self.is_admin else self.city_cb.get().strip()
        city_label = city_name if city_name and city_name != "All Cities" else "All Cities"

        self._toggle_financial_filters(report_key == "Financial")
        self._toggle_maintenance_filters(report_key == "Maintenance")

        if report_key == "Occupancy":
            rows = self._fetch_occupancy_rows(city_id=city_id)
            self._render_table(
                title=f"Occupancy Report - {city_label}",
                columns=("id", "city", "building", "type", "rooms", "status"),
                headings=("Apartment", "City", "Building", "Type", "Rooms", "Status"),
                widths=(90, 120, 230, 110, 80, 120),
                rows=rows,
            )
            return

        if report_key == "Financial":
            late_filter_value, paid_filter_value = self._get_financial_filter_values()
            rows = self._fetch_financial_rows(
                city_id=city_id,
                late_filter=late_filter_value,
                paid_filter=paid_filter_value,
            )
            self._render_table(
                title=f"Financial Summary - {city_label}",
                columns=("payment_id", "city", "tenant", "due", "amount", "is_paid", "is_late"),
                headings=("Payment ID", "City", "Tenant", "Due Date", "Amount", "Paid", "Is Late"),
                widths=(95, 110, 180, 120, 100, 85, 95),
                rows=rows,
            )
            return

        if report_key == "Maintenance":
            all_rows = self._fetch_maintenance_rows(city_id=city_id)
            self._load_building_filter_options(all_rows)

            selected_building = (self.building_filter_cb.get() or "All Buildings").strip()
            if selected_building == "All Buildings":
                filtered_rows = all_rows
            else:
                filtered_rows = [row for row in all_rows if str(row[2]).strip() == selected_building]

            # Row shape: (request_id, city, building, issue, status, cost, resolved)
            if self.role == "Manager":
                rows = filtered_rows
                columns = ("request_id", "city", "building", "issue", "status", "cost", "resolved")
                headings = ("Request ID", "City", "Building", "Issue", "Status", "Cost", "Resolved")
                widths = (90, 90, 105, 190, 115, 90, 110)
            else:
                rows = [(r[0], r[2], r[3], r[4], r[5], r[6]) for r in filtered_rows]
                columns = ("request_id", "building", "issue", "status", "cost", "resolved")
                headings = ("Request ID", "Building", "Issue", "Status", "Cost", "Resolved")
                widths = (95, 120, 230, 130, 100, 120)

            self._render_table(
                title=f"Maintenance Cost Tracking - {city_label}",
                columns=columns,
                headings=headings,
                widths=widths,
                rows=rows,
            )
            return


def create_page(parent, user_info=None):
    page = ReportManagementPage(parent, user_info=user_info)
    page.frame.on_show = page.on_show
    return page.frame