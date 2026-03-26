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
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.selected_lease_id = None
        self.selected_lease_row = None
        self._build_layout()
        self._load_leases()


    # ================= LAYOUT =================

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

        table_wrap, self.tree = create_scrollable_treeview(
            parent=content_frame,
            columns=("id", "tenant", "apartment", "start", "end", "rent", "status"),
            headings=("ID", "Tenant", "Apartment", "Start Date", "End Date", "Rent (£)", "Status"),
            widths=(60, 180, 260, 120, 120, 120, 120),
            anchors=("center", "w", "w", "center", "center", "center", "center"),
            height=9
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        self.form_frame = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.form_frame.pack(fill="x", pady=(10, 0))

        self._build_form()

    # ================= LOAD =================

    def _load_leases(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.tree.tag_configure("Active",     background="#E8F5E9", foreground="#2E7D32")
        self.tree.tag_configure("Terminated", background="#FFEBEE", foreground="#C62828")
        self.tree.tag_configure("Expired",    background="#FFF8E1", foreground="#F57F17")

        # Sort priority: Active first, then Expired, then Terminated
        priority = {"Active": 0, "Expired": 1, "Terminated": 2}
        leases = sorted(fetch_leases(), key=lambda lease: priority.get(lease[8], 99))

        for lease in leases:
            (l_id, _apt_id, _ten_id,
             tenant_name, apt_display,
             start, end, rent, status) = lease

            self.tree.insert(
                "", "end",
                values=(
                    l_id, tenant_name, apt_display,
                    start, end, f"£{float(rent):,.2f}", status,
                ),
                tags=(status,),
            )

    # ================= EVENTS =================

    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_lease_id  = values[0]
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
        self.tenant_map = build_tenant_map(fetch_tenants())
        self.available_map = build_apartment_map(fetch_available_apartments())

        self.tenant_cb = ttk.Combobox(self.form_frame, values=list(self.tenant_map.keys()), state="readonly")
        self.apt_cb = ttk.Combobox(self.form_frame, values=list(self.available_map.keys()), state="readonly")

        self.first_name_entry = None  # placeholder to keep method naming consistent

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

        tk.Button(
            self.form_frame,
            text="Create Lease",
            bg="#3B86FF",
            fg="white",
            font=("Arial", 12, "bold"),
            command=self._add_lease,
            relief="flat",
            bd=0,
            padx=14,
            pady=8
        ).grid(row=2, column=3, padx=16, pady=8, sticky="e")

        self.form_frame.grid_columnconfigure(1, weight=1)
        self.form_frame.grid_columnconfigure(3, weight=1)

    # ================= ACTIONS =================

    def _add_lease(self):
        if not self.tenant_cb.get() or not self.apt_cb.get():
            messagebox.showerror("Validation Error", "Please choose tenant and apartment.")
            return

        try:
            create_lease(
                build_apartment_map(fetch_available_apartments())[self.apt_cb.get()],
                build_tenant_map(fetch_tenants())[self.tenant_cb.get()],
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

        values   = self.selected_lease_row
        end_str  = values[4]
        rent_str = values[5].replace("£", "").replace(",", "")
        status   = values[6]

        if status == "Terminated":
            messagebox.showinfo("Info", "This lease is already terminated.")
            return

        is_early = date.fromisoformat(str(end_str)) > date.today()
        penalty  = round(float(rent_str) * 0.05, 2) if is_early else 0.00
        vacate   = str(date.today() + timedelta(days=30)) if is_early else end_str

        msg = (
            f"Tenant:       {values[1]}\n"
            f"Apartment:    {values[2]}\n"
            f"Lease End:    {end_str}\n"
            f"Vacate By:    {vacate}\n"
        )
        if is_early:
            msg += f"Penalty (5%): £{penalty:,.2f}\n\nEarly termination — 1 month notice + 5% penalty applies."
        else:
            msg += "No penalty (end of term)."

        if not messagebox.askyesno("Confirm Removal", msg):
            return

        try:
            update_lease_early_termination(int(self.selected_lease_id), penalty)
            self.selected_lease_id  = None
            self.selected_lease_row = None
            self._load_leases()
        except Exception as e:
            messagebox.showerror("Error", str(e))
