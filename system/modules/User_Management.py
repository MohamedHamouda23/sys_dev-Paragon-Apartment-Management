import tkinter as tk
from tkinter import messagebox, ttk

from main.helpers import create_button
from database.user_service import (
    get_all_users,
    get_all_roles,
    get_all_locations,
    create_user,
    update_user,
    delete_user,
)


class UserManagementPage:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self.selected_user_id = None

        self.roles = []
        self.role_name_to_id = {}
        self.cities = []
        self.city_name_to_id = {}

        self._build_layout()
        self._load_lookups()
        self._load_users()

    def _build_layout(self):
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        create_button(
            btns_inner_frame,
            text="Add user",
            width=140,
            height=45,
            bg="#3B86FF",
            fg="white",
            command=self.add_user,
        ).pack(side="left", padx=8)

        create_button(
            btns_inner_frame,
            text="Update user",
            width=140,
            height=45,
            bg="#3B86FF",
            fg="white",
            command=self.update_user,
        ).pack(side="left", padx=8)

        create_button(
            btns_inner_frame,
            text="Delete user",
            width=140,
            height=45,
            bg="#3B86FF",
            fg="white",
            command=self.delete_user,
        ).pack(side="left", padx=8)

        create_button(
            btns_inner_frame,
            text="Clear",
            width=120,
            height=45,
            bg="#3B86FF",
            fg="white",
            command=self.clear_form,
        ).pack(side="left", padx=8)

        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        table_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, pady=(0, 12))

        columns = ("id", "first_name", "surname", "email", "city", "role")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=9)

        self.tree.heading("id", text="ID")
        self.tree.heading("first_name", text="First Name")
        self.tree.heading("surname", text="Surname")
        self.tree.heading("email", text="Email")
        self.tree.heading("city", text="City")
        self.tree.heading("role", text="Role")

        self.tree.column("id", width=55, anchor="center")
        self.tree.column("first_name", width=140, anchor="w")
        self.tree.column("surname", width=140, anchor="w")
        self.tree.column("email", width=210, anchor="w")
        self.tree.column("city", width=140, anchor="w")
        self.tree.column("role", width=170, anchor="w")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        form = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        form.pack(fill="x", padx=0)

        self.first_name_entry = self._form_field(form, "First Name", 0, 0)
        self.surname_entry = self._form_field(form, "Surname", 0, 2)
        self.email_entry = self._form_field(form, "Email", 1, 0)
        self.password_entry = self._form_field(form, "Password", 1, 2, show="*")

        tk.Label(form, text="Role", bg="white", font=("Arial", 11, "bold")).grid(
            row=2, column=0, padx=(16, 6), pady=8, sticky="w"
        )
        self.role_combobox = ttk.Combobox(form, state="readonly", width=28)
        self.role_combobox.grid(row=2, column=1, padx=(0, 16), pady=8, sticky="we")

        tk.Label(form, text="City", bg="white", font=("Arial", 11, "bold")).grid(
            row=2, column=2, padx=(16, 6), pady=8, sticky="w"
        )
        self.city_combobox = ttk.Combobox(form, state="readonly", width=28)
        self.city_combobox.grid(row=2, column=3, padx=(0, 16), pady=8, sticky="we")

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

    def _form_field(self, parent, label, row, col, show=None):
        tk.Label(parent, text=label, bg="white", font=("Arial", 11, "bold")).grid(
            row=row, column=col, padx=(16, 6), pady=8, sticky="w"
        )
        entry = tk.Entry(parent, width=30, show=show)
        entry.grid(row=row, column=col + 1, padx=(0, 16), pady=8, sticky="we")
        return entry

    def _load_lookups(self):
        self.roles = get_all_roles()
        self.role_name_to_id = {name: role_id for role_id, name in self.roles}
        role_names = list(self.role_name_to_id.keys())
        self.role_combobox["values"] = role_names

        self.cities = get_all_locations()
        self.city_name_to_id = {name: city_id for city_id, name in self.cities}
        city_names = list(self.city_name_to_id.keys())
        self.city_combobox["values"] = city_names

        if role_names:
            self.role_combobox.set(role_names[0])
        if city_names:
            self.city_combobox.set(city_names[0])

    def _load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for user in get_all_users():
            self.tree.insert("", "end", values=user)

    def _on_row_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        user_values = self.tree.item(selected[0], "values")
        self.selected_user_id = int(user_values[0])

        self.first_name_entry.delete(0, tk.END)
        self.first_name_entry.insert(0, user_values[1])

        self.surname_entry.delete(0, tk.END)
        self.surname_entry.insert(0, user_values[2])

        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, user_values[3])

        self.password_entry.delete(0, tk.END)

        city_name = user_values[4]
        role_name = user_values[5]

        if city_name in self.city_name_to_id:
            self.city_combobox.set(city_name)
        if role_name in self.role_name_to_id:
            self.role_combobox.set(role_name)

    def _collect_form_data(self, require_password):
        first_name = self.first_name_entry.get().strip()
        surname = self.surname_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role_name = self.role_combobox.get().strip()
        city_name = self.city_combobox.get().strip()

        if not first_name or not surname or not email or not role_name:
            raise ValueError("First name, surname, email and role are required.")

        if require_password and not password:
            raise ValueError("Password is required when adding a user.")

        role_id = self.role_name_to_id.get(role_name)
        if role_id is None:
            raise ValueError("Please select a valid role.")

        city_id = self.city_name_to_id.get(city_name)
        return first_name, surname, email, password, role_id, city_id

    def add_user(self):
        try:
            first_name, surname, email, password, role_id, city_id = self._collect_form_data(require_password=True)
            create_user(first_name, surname, email, password, role_id, city_id)
            self._load_users()
            self.clear_form()
            messagebox.showinfo("Success", "User added successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def update_user(self):
        if self.selected_user_id is None:
            messagebox.showerror("Selection Error", "Please select a user from the table first.")
            return

        try:
            first_name, surname, email, password, role_id, city_id = self._collect_form_data(require_password=False)
            update_user(
                self.selected_user_id,
                first_name,
                surname,
                email,
                role_id,
                city_id,
                password_hash=password if password else None,
            )
            self._load_users()
            messagebox.showinfo("Success", "User updated successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def delete_user(self):
        if self.selected_user_id is None:
            messagebox.showerror("Selection Error", "Please select a user from the table first.")
            return

        confirmed = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?")
        if not confirmed:
            return

        try:
            delete_user(self.selected_user_id)
            self._load_users()
            self.clear_form()
            messagebox.showinfo("Success", "User deleted successfully.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def clear_form(self):
        self.selected_user_id = None
        self.tree.selection_remove(self.tree.selection())

        self.first_name_entry.delete(0, tk.END)
        self.surname_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

        role_names = list(self.role_name_to_id.keys())
        city_names = list(self.city_name_to_id.keys())

        if role_names:
            self.role_combobox.set(role_names[0])
        else:
            self.role_combobox.set("")

        if city_names:
            self.city_combobox.set(city_names[0])
        else:
            self.city_combobox.set("")


def create_page(parent):
    return UserManagementPage(parent).frame
