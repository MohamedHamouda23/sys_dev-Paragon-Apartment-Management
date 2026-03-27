import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date, timedelta

from main.helpers import create_button, create_scrollable_treeview
from database.lease_service import (
    fetch_leases,
    create_lease,
    fetch_tenants,
    build_tenant_map,
    fetch_available_apartments,
    build_apartment_map,
    update_lease_early_termination,
)


class LeaseManagerPage:
    def __init__(self, parent, user_info=None):
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.selected_lease_id = None
        self.selected_lease_row = None

        self.user_id = None
        self.user_role = None
        self.assigned_city_id = None
        self.tenant_id = None

        self.all_leases = []
        self.city_filter_var = tk.StringVar(value="All Cities")

        from database.tenant_portal_service import get_tenant_id_from_user

        if user_info and len(user_info) >= 6:
            self.user_id = user_info[0]
            self.user_role = user_info[4]
            self.assigned_city_id = user_info[5]
            self.tenant_id = get_tenant_id_from_user(self.user_id)

        self._build_layout()
        self._load_leases()

    def _get_filtered_manager_leases(self):
        if self.user_role != "Manager":
            return self.all_leases

        selected_city = "All Cities"
        if hasattr(self, "city_filter_cb") and self.city_filter_cb.winfo_exists():
            selected_city = (self.city_filter_cb.get() or "All Cities").strip()
        else:
            selected_city = (self.city_filter_var.get() or "All Cities").strip()

        if selected_city == "All Cities":
            return self.all_leases

        return [
            lease for lease in self.all_leases
            if str(lease[6]).strip() == selected_city
        ]

    def _refresh_manager_city_filter(self):
        if self.user_role != "Manager" or not hasattr(self, "city_filter_cb"):
            return

        current_value = (self.city_filter_cb.get() or "All Cities").strip()

        cities = sorted({str(lease[6]).strip() for lease in self.all_leases if lease[6]})
        values = ["All Cities"] + cities
        self.city_filter_cb["values"] = values

        if current_value in values:
            self.city_filter_cb.set(current_value)
            self.city_filter_var.set(current_value)
        else:
            self.city_filter_cb.set("All Cities")
            self.city_filter_var.set("All Cities")

    def _load_leases(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.tree.tag_configure("Active", background="#E8F5E9", foreground="#2E7D32")
        self.tree.tag_configure("Terminated", background="#FFEBEE", foreground="#C62828")
        self.tree.tag_configure("Expired", background="#FFF8E1", foreground="#F57F17")

        leases = []

        if self.user_role == "Tenant":
            leases = fetch_leases(tenant_id=self.tenant_id, city_id=self.assigned_city_id)
        elif self.user_role == "Manager":
            self.all_leases = fetch_leases()
            self._refresh_manager_city_filter()
            leases = self._get_filtered_manager_leases()
        elif self.user_role in ["Administrators", "Front-desk Staff"]:
            leases = fetch_leases(city_id=self.assigned_city_id)
        else:
            leases = fetch_leases(city_id=self.assigned_city_id)

        priority = {"Active": 0, "Expired": 1, "Terminated": 2}
        leases = sorted(leases, key=lambda lease: priority.get(lease[7], 99))

        for lease in leases:
            (l_id, tenant_name, apt_display, start, end, rent, city_val, status) = lease
            self.tree.insert(
                "",
                "end",
                values=(
                    l_id,
                    tenant_name,
                    apt_display,
                    start,
                    end,
                    f"£{float(rent):,.2f}",
                    city_val,
                    status,
                ),
                tags=(status,),
            )

    def _on_manager_city_filter_change(self, event=None):
        if self.user_role != "Manager":
            return

        selected_city = (event.widget.get() if event else self.city_filter_cb.get() or "All Cities").strip()
        self.city_filter_var.set(selected_city)

        for row in self.tree.get_children():
            self.tree.delete(row)

        leases = self._get_filtered_manager_leases()

        priority = {"Active": 0, "Expired": 1, "Terminated": 2}
        leases = sorted(leases, key=lambda lease: priority.get(lease[7], 99))

        for lease in leases:
            (l_id, tenant_name, apt_display, start, end, rent, city_val, status) = lease
            self.tree.insert(
                "",
                "end",
                values=(
                    l_id,
                    tenant_name,
                    apt_display,
                    start,
                    end,
                    f"£{float(rent):,.2f}",
                    city_val,
                    status,
                ),
                tags=(status,),
            )

    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner.pack(anchor="center")

        create_button(btns_inner, "Add Lease", 140, 45, "#3B86FF", "white", self._add_lease).pack(side="left", padx=8)
        create_button(btns_inner, "Remove Lease", 140, 45, "#3B86FF", "white", self._remove_lease).pack(side="left", padx=8)
        create_button(btns_inner, "Track Lease", 140, 45, "#3B86FF", "white", self._load_leases).pack(side="left", padx=8)

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        tk.Label(content_frame, text="Lease Information", bg="#c9e4c4", font=("Arial", 16, "bold")).pack(pady=(0, 10))

        if self.user_role == "Manager":
            filter_frame = tk.Frame(content_frame, bg="#c9e4c4")
            filter_frame.pack(fill="x", pady=(0, 10))

            tk.Label(
                filter_frame,
                text="Filter by City:",
                bg="#c9e4c4",
                font=("Arial", 11, "bold")
            ).pack(side="left", padx=(0, 8))

            self.city_filter_cb = ttk.Combobox(
                filter_frame,
                textvariable=self.city_filter_var,
                state="readonly",
                values=["All Cities"],
                width=22
            )
            self.city_filter_cb.pack(side="left")
            self.city_filter_cb.bind("<<ComboboxSelected>>", self._on_manager_city_filter_change)

        table_wrap, self.tree = create_scrollable_treeview(
            parent=content_frame,
            columns=("id", "tenant", "apartment", "start", "end", "rent", "city", "status"),
            headings=("ID", "Tenant", "Apartment", "Start Date", "End Date", "Rent (£)", "City", "Status"),
            widths=(60, 180, 260, 120, 120, 120, 120, 120),
            anchors=("center", "w", "w", "center", "center", "center", "center", "center"),
            height=9
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        self.form_frame = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.form_frame.pack(fill="x", pady=(10, 0))

        self._build_form()

    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_lease_id = values[0]
        self.selected_lease_row = values

    def _form_field(self, parent, label, row, col):
        tk.Label(parent, text=label, bg="white", font=("Arial", 11, "bold")).grid(
            row=row, column=col, padx=(16, 6), pady=8, sticky="w"
        )

    def _clear_form(self):
        self.tenant_cb.set("")
        self.apt_cb.set("")
        self.start_entry.delete(0, tk.END)
        self.end_entry.delete(0, tk.END)
        self.rent_entry.delete(0, tk.END)

    def _build_form(self):
        if self.user_role == "Administrators":
            tenants = fetch_tenants(city_id=self.assigned_city_id)
            apartments = fetch_available_apartments(city_id=self.assigned_city_id)
        elif self.user_role == "Tenant":
            tenants = fetch_tenants(tenant_id=self.tenant_id)
            apartments = fetch_available_apartments(city_id=None)
        else:
            tenants = fetch_tenants(city_id=None)
            apartments = fetch_available_apartments(city_id=None)

        self.tenant_map = {t[1]: t for t in tenants}
        self.available_map = build_apartment_map(apartments)

        self.tenant_cb = ttk.Combobox(self.form_frame, values=list(self.tenant_map.keys()), state="readonly")
        self.apt_cb = ttk.Combobox(self.form_frame, values=list(self.available_map.keys()), state="readonly")

        self._form_field(self.form_frame, "Tenant", 0, 0)
        self.tenant_cb.grid(row=0, column=1, padx=(0, 16), pady=8, sticky="we")

        self._form_field(self.form_frame, "Apartment (Vacant)", 0, 2)
        self.apt_cb.grid(row=0, column=3, padx=(0, 16), pady=8, sticky="we")

        today = date.today()

        self._form_field(self.form_frame, "Start Date", 1, 0)
        self.start_entry = tk.Entry(self.form_frame)
        self.start_entry.insert(0, str(today))
        self.start_entry.grid(row=1, column=1, padx=(0, 16), pady=8, sticky="we")

        self._form_field(self.form_frame, "End Date", 1, 2)
        self.end_entry = tk.Entry(self.form_frame)
        self.end_entry.insert(0, str(today.replace(year=today.year + 1)))
        self.end_entry.grid(row=1, column=3, padx=(0, 16), pady=8, sticky="we")

        self._form_field(self.form_frame, "Monthly Rent (£)", 2, 0)
        self.rent_entry = tk.Entry(self.form_frame)
        self.rent_entry.grid(row=2, column=1, padx=(0, 16), pady=8, sticky="we")

        self.form_frame.grid_columnconfigure(1, weight=1)
        self.form_frame.grid_columnconfigure(3, weight=1)

    def _add_lease(self):
        if not self.tenant_cb.get() or not self.apt_cb.get():
            messagebox.showerror("Validation Error", "Please choose tenant and apartment.")
            return

        try:
            create_lease(
                self.available_map[self.apt_cb.get()],
                self.tenant_map[self.tenant_cb.get()][0],
                self.start_entry.get(),
                self.end_entry.get(),
                self.rent_entry.get()
            )
            messagebox.showinfo("Success", "Lease created!")
            self._clear_form()
            self._load_leases()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _remove_lease(self):
        if not self.selected_lease_id:
            messagebox.showerror("Error", "Please select a lease first.")
            return

        values = self.selected_lease_row
        end_str = values[4]
        rent_str = values[5].replace("£", "").replace(",", "")
        status = values[7]

        if status == "Terminated":
            messagebox.showinfo("Info", "This lease is already terminated.")
            return

        is_early = date.fromisoformat(str(end_str)) > date.today()
        penalty = round(float(rent_str) * 0.05, 2) if is_early else 0.00
        vacate = str(date.today() + timedelta(days=30)) if is_early else end_str

        msg = f"Tenant: {values[1]}\nApartment: {values[2]}\nLease End: {end_str}\nVacate By: {vacate}\n"
        if is_early:
            msg += f"Penalty (5%): £{penalty:,.2f}\n\nEarly termination applies."

        if not messagebox.askyesno("Confirm Removal", msg):
            return

        try:
            update_lease_early_termination(int(self.selected_lease_id), penalty)
            self.selected_lease_id = None
            self.selected_lease_row = None
            self._load_leases()
        except Exception as e:
            messagebox.showerror("Error", str(e))