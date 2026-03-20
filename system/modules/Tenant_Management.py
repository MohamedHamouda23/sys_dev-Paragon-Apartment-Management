import tkinter as tk
from tkinter import ttk, messagebox


from main.helpers import (
    create_button, create_frame, clear_frame, styled_label, form_field, form_dropdown, card, BG, ACCENT, FONT_TITLE, FONT_LABEL 
)

from database.tenant_management_service import (
    get_all_tenants,
    create_tenant,
    update_tenant,
    delete_tenant,
    get_all_complaints_with_tenant
)


class TenantManagementPage:
    def __init__(self, parent):
        print("TENANT PAGE LOADED FROM:", __file__)
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.selected_tenant_id = None

        self._build_layout()
        self._load_tenants()

    # ---------------------------------------------------
    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        create_button(btns_inner_frame, "Add Tenant", 140, 45, "#3B86FF", "white", self.add_tenant).pack(side="left", padx=8)
        create_button(btns_inner_frame, "Update Tenant", 140, 45, "#3B86FF", "white", self.update_tenant).pack(side="left", padx=8)
        create_button(btns_inner_frame, "Delete Tenant", 140, 45, "#3B86FF", "white", self.delete_tenant).pack(side="left", padx=8)
        create_button(btns_inner_frame, "View Complaints", 160, 45, "#3B86FF", "white", self.view_complaints).pack(side="left", padx=8)

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        tk.Label(content_frame, text="Tenant Information", bg="#c9e4c4", font=("Arial", 16, "bold")).pack(pady=(0, 10))

        table_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, pady=(0, 12))

        columns = (
            "tenant_id", "first_name", "surname", "email", "telephone",
            "reference_name", "reference_email", "ni_number",
            "lease_period", "apartment_type", "occupation"
        )

        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=9)

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())

        self.tree.column("tenant_id", width=55, anchor="center")
        self.tree.column("first_name", width=120)
        self.tree.column("surname", width=120)
        self.tree.column("email", width=180)
        self.tree.column("telephone", width=120)
        self.tree.column("reference_name", width=150)
        self.tree.column("reference_email", width=180)
        self.tree.column("ni_number", width=150)
        self.tree.column("lease_period", width=120)
        self.tree.column("apartment_type", width=140)
        self.tree.column("occupation", width=140)

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        form = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        form.pack(fill="x", padx=0)

        self.first_name_entry = self._form_field(form, "First Name", 0, 0)
        self.surname_entry = self._form_field(form, "Surname", 0, 2)
        self.email_entry = self._form_field(form, "Email", 0, 4)

        self.telephone_entry = self._form_field(form, "Telephone", 1, 0)
        self.reference_name_entry = self._form_field(form, "Reference Name", 1, 2)
        self.reference_email_entry = self._form_field(form, "Reference Email", 1, 4)

        self.ni_entry = self._form_field(form, "National Insurance Number", 2, 0)
        self.lease_period_entry = self._form_field(form, "Lease Period", 2, 2)
        self.apartment_type_entry = self._form_field(form, "Apartment Type", 2, 4)

        self.occupation_entry = self._form_field(form, "Occupation", 3, 0)

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)
        form.grid_columnconfigure(5, weight=1)

    # ---------------------------------------------------
    def _form_field(self, parent, label, row, col):
        tk.Label(parent, text=label, bg="white", font=("Arial", 11, "bold")).grid(
            row=row, column=col, padx=(16, 6), pady=8, sticky="w"
        )
        entry = tk.Entry(parent, width=30)
        entry.grid(row=row, column=col + 1, padx=(0, 16), pady=8, sticky="we")
        return entry

    # ---------------------------------------------------
    def _load_tenants(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for tenant in get_all_tenants():
            self.tree.insert("", "end", values=tenant)

    # ---------------------------------------------------
    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        self.selected_tenant_id = int(values[0])

        entries = [
            self.first_name_entry, self.surname_entry, self.email_entry,
            self.telephone_entry, self.reference_name_entry, self.reference_email_entry,
            self.ni_entry, self.lease_period_entry, self.apartment_type_entry,
            self.occupation_entry
        ]

        for entry, value in zip(entries, values[1:]):
            entry.delete(0, tk.END)
            entry.insert(0, value)

    # ---------------------------------------------------
    def add_tenant(self):
        try:
            data = self._collect_form_data()
            create_tenant(*data)
            self._load_tenants()
            messagebox.showinfo("Success", "Tenant added successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    # ---------------------------------------------------
    def update_tenant(self):
        if self.selected_tenant_id is None:
            messagebox.showerror("Selection Error", "Please select a tenant first.")
            return

        try:
            data = self._collect_form_data()
            update_tenant(self.selected_tenant_id, *data)
            self._load_tenants()
            messagebox.showinfo("Success", "Tenant updated successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    # ---------------------------------------------------
    def delete_tenant(self):
        if self.selected_tenant_id is None:
            messagebox.showerror("Selection Error", "Please select a tenant first.")
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this tenant?"):
            return

        try:
            delete_tenant(self.selected_tenant_id)
            self.selected_tenant_id = None
            self._load_tenants()
            messagebox.showinfo("Success", "Tenant deleted successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    # ---------------------------------------------------
    def _collect_form_data(self):
        return (
            self.first_name_entry.get().strip(),
            self.surname_entry.get().strip(),
            self.email_entry.get().strip(),
            self.telephone_entry.get().strip(),
            self.reference_name_entry.get().strip(),
            self.reference_email_entry.get().strip(),
            self.ni_entry.get().strip(),
            self.lease_period_entry.get().strip(),
            self.apartment_type_entry.get().strip(),
            self.occupation_entry.get().strip(),
        )

    # ---------------------------------------------------
    # GLOBAL COMPLAINT VIEWER (NO TENANT SELECTION REQUIRED)
    # ---------------------------------------------------
    def view_complaints(self):
        win = tk.Toplevel(self.frame)
        win.title("All Tenant Complaints")
        win.geometry("900x500")
        win.config(bg="#c9e4c4")

        tk.Label(win, text="All Tenant Complaints",
                 bg="#c9e4c4", font=("Arial", 16, "bold")).pack(pady=10)

        table_wrap = tk.Frame(win, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("complaint_id", "tenant_id", "name", "description", "date_submitted")
        tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=15)

        tree.heading("complaint_id", text="Complaint ID")
        tree.heading("tenant_id", text="Tenant ID")
        tree.heading("name", text="Tenant Name")
        tree.heading("description", text="Complaint")
        tree.heading("date_submitted", text="Date Submitted")

        tree.column("complaint_id", width=100, anchor="center")
        tree.column("tenant_id", width=100, anchor="center")
        tree.column("name", width=180)
        tree.column("description", width=350)
        tree.column("date_submitted", width=150)

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=y_scroll.set)

        tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

        complaints = get_all_complaints_with_tenant()

        for c in complaints:
            complaint_id, tenant_id, first, surname, desc, date = c
            tree.insert("", "end", values=(
                complaint_id,
                tenant_id,
                f"{first} {surname}",
                desc,
                date
            ))


def create_page(parent):
    return TenantManagementPage(parent).frame
