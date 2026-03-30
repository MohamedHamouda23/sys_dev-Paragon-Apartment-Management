import tkinter as tk
from tkinter import ttk, messagebox
from database.property_service import get_all_cities
from main.helpers import create_button
from database.report_service import (
    fetch_summary_snapshot, fetch_occupancy_rows,
    fetch_financial_rows, fetch_maintenance_rows,
    log_report_generation
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
        self.user_id = user_info[0] if user_info else None
        self.role = user_info[4] if user_info and len(user_info) > 4 else None
        self.assigned_city_id = user_info[5] if user_info and len(user_info) > 5 else None

        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.logic = ReportLogicHandler(self)

        self.city_name_to_id = {}
        self.available_report_types = self._get_allowed_report_types()

        # Tenants are restricted users
        self.is_admin = self.role in ["Administrators", "Maintenance Staff", "Tenant"]
        self.show_report_selector = len(self.available_report_types) > 1

        self.selected_city = tk.StringVar(value="All Cities")
        default_type = self.available_report_types[0] if self.available_report_types else "Occupancy"
        self.selected_report_type = tk.StringVar(value=default_type)

        self.late_filter = tk.StringVar(value="All")
        self.paid_filter = tk.StringVar(value="All")
        self.building_filter = tk.StringVar(value="All Buildings")

        self.summary_cards = {}
        self.summary_card_frames = {}
        self.summary_card_order = []
        self.cards_row = None
        self.tree = None
        self.current_report_title = ""
        self.current_headings = []
        self.current_rows = []

        self.city_cb = None
        self.report_cb = None
        self.building_label = None
        self.building_filter_cb = None
        self.late_filter_cb = None
        self.paid_filter_cb = None
        self.generate_btn = None
        self.report_label_to_key = {}

        self._build_layout()
        self._load_city_filter_options()
        self._refresh_building_filter_options()
        self.generate_report()

    def _get_allowed_report_types(self):
        full_access = ["Occupancy", "Financial", "Maintenance"]
        permissions = {
            "Administrators": full_access,
            "Manager": full_access,
            "Maintenance Staff": ["Maintenance"],
            "Finance Manager": ["Financial"]
        }
        return permissions.get(self.role, full_access)

    def _build_layout(self):
        top_wrap = tk.Frame(self.frame, bg="#c9e4c4")
        top_wrap.pack(fill="x", padx=24, pady=(20, 8))

        controls = tk.Frame(top_wrap, bg="#c9e4c4")
        controls.pack(anchor="center")

        # City filter
        if self.role == "Manager":
            tk.Label(
                controls, text="City:", bg="#c9e4c4", fg="#1f3b63",
                font=("Arial", 11, "bold")
            ).pack(side="left", padx=(0, 8))

            self.city_cb = ttk.Combobox(
                controls,
                textvariable=self.selected_city,
                values=["All Cities"],
                state="readonly",
                width=18,
                font=("Arial", 10)
            )
            self.city_cb.pack(side="left", padx=(0, 14))
            self.city_cb.bind("<<ComboboxSelected>>", self._on_city_change)

        # Report selector
        if self.show_report_selector:
            tk.Label(
                controls, text="Report:", bg="#c9e4c4", fg="#1f3b63",
                font=("Arial", 11, "bold")
            ).pack(side="left", padx=(0, 8))

            report_labels = [REPORT_TYPES[r] for r in self.available_report_types]
            self.report_label_to_key = {REPORT_TYPES[key]: key for key in self.available_report_types}

            self.report_cb = ttk.Combobox(
                controls,
                values=report_labels,
                state="readonly",
                width=46,
                font=("Arial", 10)
            )
            self.report_cb.pack(side="left", padx=(0, 14))
            self.report_cb.set(REPORT_TYPES[self.selected_report_type.get()])
            self.report_cb.bind("<<ComboboxSelected>>", self._on_report_type_change)

        # Building filter in main controls
        self.building_label = tk.Label(
            controls, text="Building:", bg="#c9e4c4", fg="#1f3b63",
            font=("Arial", 11, "bold")
        )
        self.building_label.pack(side="left", padx=(0, 8))

        self.building_filter_cb = ttk.Combobox(
            controls,
            textvariable=self.building_filter,
            values=["All Buildings"],
            state="readonly",
            width=18,
            font=("Arial", 10)
        )
        self.building_filter_cb.pack(side="left", padx=(0, 14))
        self.building_filter_cb.bind("<<ComboboxSelected>>", self._on_building_filter_change)

        self.generate_btn = create_button(
            controls,
            text="Generate",
            width=120,
            height=42,
            bg="#3B86FF",
            fg="white",
            command=self._generate_and_export
        )
        self.generate_btn.pack(side="left")

        # Financial filters
        self.financial_filter_wrap = tk.Frame(top_wrap, bg="#c9e4c4")
        for lbl, var, vals in [
            ("Late Filter:", self.late_filter, ["All", "Late", "Not Late"]),
            ("Paid Filter:", self.paid_filter, ["All", "Paid", "Not Paid"])
        ]:
            tk.Label(
                self.financial_filter_wrap,
                text=lbl,
                bg="#c9e4c4",
                fg="#1f3b63",
                font=("Arial", 10, "bold")
            ).pack(side="left", padx=(0, 6))

            cb = ttk.Combobox(
                self.financial_filter_wrap,
                textvariable=var,
                values=vals,
                state="readonly",
                width=10,
                font=("Arial", 10)
            )
            cb.pack(side="left", padx=(0, 16))
            cb.bind("<<ComboboxSelected>>", self._on_financial_filter_change)

            if lbl == "Late Filter:":
                self.late_filter_cb = cb
            elif lbl == "Paid Filter:":
                self.paid_filter_cb = cb

        summary_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        summary_wrap.pack(fill="x", padx=24, pady=(4, 10))

        tk.Label(
            summary_wrap,
            text="Report Snapshot",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#1f3b63"
        ).pack(pady=(10, 8))

        self.cards_row = tk.Frame(summary_wrap, bg="white")
        self.cards_row.pack(fill="x", padx=10, pady=(0, 10))

        all_cards = [
            ("Apartments", "0", "#3B86FF"),
            ("Occupancy", "0.0%", "#28a745"),
            ("Collected", "£0.00", "#17a2b8"),
            ("Maintenance", "£0.00", "#6c757d")
        ]

        if self.role == "Finance Manager":
            display_cards = [c for c in all_cards if c[0] in ["Apartments", "Collected"]]
        elif self.role == "Maintenance Staff":
            display_cards = [c for c in all_cards if c[0] in ["Apartments", "Maintenance"]]
        elif self.role == "Tenant":
            display_cards = [c for c in all_cards if c[0] in ["Apartments", "Maintenance"]]
        else:
            display_cards = all_cards

        for idx, (label, val, col) in enumerate(display_cards):
            card = tk.Frame(self.cards_row, bg=col, bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=5, sticky="ew")
            self.cards_row.grid_columnconfigure(idx, weight=1)

            self.summary_card_frames[label] = card
            self.summary_card_order.append(label)

            self.summary_cards[label] = tk.Label(
                card,
                text=val,
                font=("Arial", 18, "bold"),
                bg=col,
                fg="white"
            )
            self.summary_cards[label].pack(pady=(10, 2))

            tk.Label(
                card,
                text=label,
                font=("Arial", 10),
                bg=col,
                fg="white"
            ).pack(pady=(0, 9))

        results_wrap = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        results_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.results_title = tk.Label(
            results_wrap,
            text="Report Results",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#1f3b63",
            anchor="w"
        )
        self.results_title.pack(fill="x", padx=12, pady=(10, 6))

        self.table_host = tk.Frame(results_wrap, bg="white")
        self.table_host.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _update_summary_cards_visibility(self, report_key):
        """Show only relevant snapshot cards for the selected report type."""
        visible_by_report = {
            "Occupancy": {"Apartments", "Occupancy"},
            "Financial": {"Apartments", "Collected"},
            "Maintenance": {"Apartments", "Maintenance"},
        }
        requested_visible = visible_by_report.get(report_key, set(self.summary_card_order))

        visible_labels = [
            label for label in self.summary_card_order
            if label in requested_visible and label in self.summary_card_frames
        ]

        # Fallback: if role-based card set does not contain expected labels, keep current cards visible.
        if not visible_labels:
            visible_labels = [label for label in self.summary_card_order if label in self.summary_card_frames]

        for frame in self.summary_card_frames.values():
            frame.grid_forget()

        total_slots = max(1, len(self.summary_card_order))
        start_col = max(0, (total_slots - len(visible_labels)) // 2)

        for col in range(total_slots):
            self.cards_row.grid_columnconfigure(col, weight=1)

        for idx, label in enumerate(visible_labels):
            frame = self.summary_card_frames[label]
            frame.grid(row=0, column=start_col + idx, padx=5, sticky="ew")

    def _load_city_filter_options(self):
        city_rows = get_all_cities()
        self.city_name_to_id = {name: cid for cid, name in city_rows}

        if self.is_admin and self.assigned_city_id:
            assigned = next((n for n, cid in self.city_name_to_id.items() if cid == self.assigned_city_id), None)
            if assigned:
                self.selected_city.set(assigned)
            return

        if self.city_cb:
            self.city_cb["values"] = ["All Cities"] + [n for _, n in city_rows]

    def _on_city_change(self, _event=None):
        self.building_filter.set("All Buildings")
        self._refresh_building_filter_options()
        self.generate_report()

    def _on_report_type_change(self, _event=None):
        key = self.report_label_to_key.get(self.report_cb.get())
        if key:
            self.selected_report_type.set(key)

        self.building_filter.set("All Buildings")
        self._refresh_building_filter_options()
        self.generate_report()

    def _on_building_filter_change(self, _event=None):
        # Use after_idle to ensure combobox widget state is committed before refresh.
        self.frame.after_idle(self.generate_report)

    def _set_report_filter_visibility(self, report_key):
        """Show report-specific filter controls and keep layout stable."""
        if report_key == "Financial":
            if not self.financial_filter_wrap.winfo_manager():
                self.financial_filter_wrap.pack(anchor="center", pady=(8, 2))

            if self.building_label and self.building_label.winfo_manager():
                self.building_label.pack_forget()
            if self.building_filter_cb and self.building_filter_cb.winfo_manager():
                self.building_filter_cb.pack_forget()
            return

        if self.financial_filter_wrap.winfo_manager():
            self.financial_filter_wrap.pack_forget()

        if self.building_label and not self.building_label.winfo_manager():
            self.building_label.pack(side="left", padx=(0, 8), before=self.generate_btn)
        if self.building_filter_cb and not self.building_filter_cb.winfo_manager():
            self.building_filter_cb.pack(side="left", padx=(0, 14), before=self.generate_btn)

    def _on_financial_filter_change(self, _event=None):
        self.generate_report()

    def _get_financial_filter_values(self):
        """Read current financial filter values directly from combobox widgets."""
        late_value = self.late_filter.get()
        paid_value = self.paid_filter.get()

        if self.late_filter_cb is not None:
            late_value = self.late_filter_cb.get() or late_value
        if self.paid_filter_cb is not None:
            paid_value = self.paid_filter_cb.get() or paid_value

        # Keep vars in sync with widget state.
        self.late_filter.set(late_value)
        self.paid_filter.set(paid_value)
        return late_value, paid_value

    def _get_selected_building(self):
        """Read current building filter value directly from combobox widget."""
        selected = self.building_filter.get()
        if self.building_filter_cb is not None:
            selected = self.building_filter_cb.get() or selected
        self.building_filter.set(selected)
        return (selected or "All Buildings").strip()

    def _resolve_city_id(self):
        if self.is_admin and self.assigned_city_id:
            return self.assigned_city_id

        name = self.city_cb.get().strip() if self.city_cb else self.selected_city.get().strip()
        return self.city_name_to_id.get(name) if name != "All Cities" else None

    def _refresh_building_filter_options(self):
        if not self.building_filter_cb:
            return

        report_key = self.selected_report_type.get()
        city_id = self._resolve_city_id()
        building_values = ["All Buildings"]

        # Managers must pick a specific city before building-level filtering is available.
        if self.role == "Manager" and city_id is None and report_key in ("Occupancy", "Maintenance"):
            self.building_filter.set("All Buildings")
            self.building_filter_cb["values"] = ["All Buildings"]
            self.building_filter_cb.config(state="disabled")
            return

        try:
            if report_key == "Occupancy":
                rows = fetch_occupancy_rows(city_id)
                building_values += sorted({str(r[2]) for r in rows if len(r) > 2 and r[2]})
                self.building_filter_cb.config(state="readonly")

            elif report_key == "Maintenance":
                rows = fetch_maintenance_rows(city_id)

                building_values += sorted({str(r[2]) for r in rows if len(r) > 2 and r[2]})
                self.building_filter_cb.config(state="readonly")

            else:
                # Financial currently has no building field in returned rows
                self.building_filter.set("All Buildings")
                self.building_filter_cb["values"] = ["All Buildings"]
                self.building_filter_cb.config(state="disabled")
                return

        except Exception:
            building_values = ["All Buildings"]

        self.building_filter_cb["values"] = building_values
        if self.building_filter.get() not in building_values:
            self.building_filter.set("All Buildings")

    def generate_report(self):
        city_id = self._resolve_city_id()

        snapshot = fetch_summary_snapshot(city_id)

        if "Apartments" in self.summary_cards:
            self.summary_cards["Apartments"].config(text=str(snapshot["apartments"]))
        if "Occupancy" in self.summary_cards:
            self.summary_cards["Occupancy"].config(text=f"{snapshot['occupancy_rate']:.2f}%")
        if "Collected" in self.summary_cards:
            self.summary_cards["Collected"].config(text=f"£{snapshot['collected']:,.2f}")
        if "Maintenance" in self.summary_cards:
            self.summary_cards["Maintenance"].config(text=f"£{snapshot['maintenance']:,.2f}")

        report_key = self.selected_report_type.get()
        city_label = self.selected_city.get()

        self._update_summary_cards_visibility(report_key)
        self._set_report_filter_visibility(report_key)

        # keep building filter options synced
        self._refresh_building_filter_options()
        selected_building = self._get_selected_building()

        if report_key == "Occupancy":
            rows = fetch_occupancy_rows(city_id)

            if selected_building != "All Buildings":
                selected_norm = selected_building.strip().lower()
                rows = [r for r in rows if str(r[2]).strip().lower() == selected_norm]

            if "Apartments" in self.summary_cards:
                self.summary_cards["Apartments"].config(text=str(len(rows)))

            self._render_table(
                f"Occupancy Report - {city_label}",
                ("id", "city", "building", "type", "rooms", "status"),
                ("Apartment", "City", "Building", "Type", "Rooms", "Status"),
                (90, 120, 230, 110, 80, 120),
                rows
            )

        elif report_key == "Financial":
            late_value, paid_value = self._get_financial_filter_values()
            rows = fetch_financial_rows(city_id, late_value, paid_value)

            # Defensive UI-side filtering in case backend cache/module state is stale.
            paid_choice = (paid_value or "All").strip().lower()
            late_choice = (late_value or "All").strip().lower()

            if paid_choice == "paid":
                rows = [r for r in rows if str(r[5]).strip().lower() == "yes"]
            elif paid_choice == "not paid":
                rows = [r for r in rows if str(r[5]).strip().lower() == "no"]

            if late_choice == "late":
                rows = [r for r in rows if str(r[6]).strip().lower() == "yes"]
            elif late_choice == "not late":
                rows = [r for r in rows if str(r[6]).strip().lower() == "no"]

            if "Apartments" in self.summary_cards:
                self.summary_cards["Apartments"].config(text=str(len(rows)))

            self._render_table(
                "Financial Summary",
                ("pid", "city", "tenant", "due", "amt", "paid", "late"),
                ("Payment ID", "City", "Tenant", "Due Date", "Amount", "Paid", "Is Late"),
                (95, 110, 180, 120, 100, 85, 95),
                rows
            )

        elif report_key == "Maintenance":
            all_rows = fetch_maintenance_rows(city_id)

            rows = all_rows
            if selected_building != "All Buildings":
                selected_norm = selected_building.strip().lower()
                rows = [r for r in all_rows if str(r[2]).strip().lower() == selected_norm]

            if "Apartments" in self.summary_cards:
                self.summary_cards["Apartments"].config(text=str(len(rows)))

            self._render_table(
                "Maintenance Records",
                ("rid", "city", "bld", "iss", "stat", "cost", "res"),
                ("Request ID", "City", "Building", "Issue", "Status", "Cost", "Resolved"),
                (90, 90, 105, 190, 115, 90, 110),
                rows
            )

    def _render_table(self, title, columns, headings, widths, rows):
        for w in self.table_host.winfo_children():
            w.destroy()

        self.results_title.config(text=title)
        self.current_report_title = title
        self.current_headings = list(headings)
        display_rows = [
            tuple(f"{v:.2f}" if isinstance(v, float) else ("" if v is None else v) for v in r)
            for r in rows
        ]
        self.current_rows = display_rows

        if not rows:
            tk.Label(
                self.table_host,
                text="No records found.",
                font=("Arial", 12),
                bg="white"
            ).pack(pady=20)
            return

        tree = ttk.Treeview(self.table_host, columns=columns, show="headings", height=14)

        for col, head, wid in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(
                col,
                width=wid,
                anchor="center" if col in ("id", "pid", "rid", "rooms") else "w"
            )

        tree.pack(fill="both", expand=True)

        for row in display_rows:
            tree.insert("", "end", values=row)

        self.tree = tree

    def _generate_and_export(self):
        self.generate_report()
        log_report_generation(self.selected_report_type.get(), self.user_id)
        self.frame.after(100, self.logic.export_to_pdf)

    def on_show(self):
        self._load_city_filter_options()
        self._refresh_building_filter_options()
        self.generate_report()