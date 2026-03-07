import tkinter as tk
from tkinter import ttk, messagebox

from database.maintaince_service import get_all_requests, viewFull
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
                    ("View Details",  self.view_details),
                    ("View All",      self.view_all),
                ]:
            create_button(
                self.btns_inner_frame,
                text=text,
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=command,
                next_window_func=None,
                current_window=None
            ).pack(side="left", padx=15, pady=50)



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

        if hasattr(self, "detail_frame"):
            self.detail_frame.destroy()

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
        request_id = data[0]

        full_data = viewFull(request_id)

        labels = (
            "Request ID", "Issue", "Description", "Priority", "Date Submitted",
            "Resolved Date", "Status", "Notes", "Tenant", "Apt Type",
            "Postcode", "Staff", "Assigned Date", "Is Current"
        )

        self.tree.pack_forget()

        if hasattr(self, "detail_frame"):
            self.detail_frame.destroy()

        self.detail_frame = tk.Frame(self.box_frame, bg="white")
        self.detail_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Action buttons
        action_btn_frame = tk.Frame(self.detail_frame, bg="white")
        action_btn_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 15))

        assign_btn = create_button(
            action_btn_frame,
            text="Assign Staff",
            width=130,
            height=40,
            bg="#3B86FF",
            fg="white",
            command=lambda: messagebox.showinfo("Assign Staff", "Assign Staff function not defined")
        )
        assign_btn.pack(side="left", padx=(0, 10))

        approve_btn = create_button(
            action_btn_frame,
            text="Approve",
            width=100,
            height=40,
            bg="#28A745",
            fg="white",
            command=lambda: messagebox.showinfo("Approve", "Approve function not defined")
        )
        approve_btn.pack(side="left", padx=(0, 10))

        deny_btn = create_button(
            action_btn_frame,
            text="Deny",
            width=100,
            height=40,
            bg="#FF3B3B",
            fg="white",
            command=lambda: messagebox.showinfo("Deny", "Deny function not defined")
        )
        deny_btn.pack(side="left")

        # Detail fields
        for i, (label, value) in enumerate(zip(labels, full_data)):

            tk.Label(
                self.detail_frame,
                text=f"{label}:",
                font=("Arial", 10, "bold"),
                bg="white"
            ).grid(row=i + 1, column=0, sticky="w", padx=10, pady=3)

            tk.Label(
                self.detail_frame,
                text=value,
                bg="white"
            ).grid(row=i + 1, column=1, sticky="w", padx=10, pady=3)

    # ---------------------------------------------------
    def view_all(self):

        if hasattr(self, "detail_frame"):
            self.detail_frame.destroy()

        self.populate_maintenance_requests()


# -------------------------------------------------------
def create_page(parent):
    return MaintenancePage(parent).frame