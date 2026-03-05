import tkinter as tk
from tkinter import ttk, messagebox

from database.maintaince_service import get_all_requests
from main.helpers import create_button, create_frame


# -------------------------------------------------------
class MaintenancePage:
    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)

        self.create_buttons()
        self.create_maintenance_box()

        self.populate_maintenance_requests()

    # ---------------------------------------------------
    def create_buttons(self):
    
        for text, command in [
            ("View Details", self.view_details),
            ("View All", self.view_all),
        ]:

            create_button(
                self.btns_inner_frame,
                text=text,
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=command
            ).pack(side="left")

        logout_btn = create_button(
            self.btns_inner_frame,
            text="➜",
            width=35,
            height=35,
            bg="#FF3B3B",
            fg="white",
            command=lambda: messagebox.showinfo("Logout", "Logout function not defined")
        )
        logout_btn.pack(anchor="ne", padx=10)

    # ---------------------------------------------------
    def create_maintenance_box(self):

        self.box_frame.config(bg="white", bd=2, relief="groove")
        self.box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

        self.placeholder_label = tk.Label(
            self.box_frame,
            text="Registered maintenance requests will appear here",
            font=("Arial", 16),
            bg="white",
            fg="#888"
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    # ---------------------------------------------------
    def populate_maintenance_requests(self):

        maintenance = get_all_requests()

        if not maintenance:
            return

        if hasattr(self, "tree"):
            self.tree.destroy()

        if hasattr(self, "placeholder_label"):
            self.placeholder_label.destroy()

        columns = ("Request ID", "Tenant", "Issue", "Date Submitted", "Status")

        self.tree = ttk.Treeview(self.box_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        for row in maintenance:
            self.tree.insert("", "end", values=row)

        self.tree.pack(fill="both", expand=True)

    # ---------------------------------------------------
    def view_details(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select a request first")
            return

        item = self.tree.item(selected[0])
        data = item["values"]

        # clear table
        for i in self.tree.get_children():
            self.tree.delete(i)

        # show only selected request
        self.tree.insert("", "end", values=data)

    # ---------------------------------------------------
    def view_all(self):

        self.populate_maintenance_requests()


# -------------------------------------------------------
def create_page(parent):
    return MaintenancePage(parent).frame