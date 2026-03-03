import tkinter as tk
from tkinter import ttk, messagebox

from database.maintaince_service import get_all_requests
from main.helpers import create_button, create_frame

# -------------------------------------------------------
class MaintenancePage:
    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        
        # Create UI
        self.create_buttons()
        self.create_maintenance_box()
        
        self.populate_maintenance_requests()

    # ---------------------------------------------------
    def create_buttons(self):
        logout_btn = create_button(
            self.btns_inner_frame,
            text="➜",
            width=35,
            height=35,
            bg="#FF3B3B",
            fg="white",
            command=lambda: messagebox.showinfo("Logout", "Logout function not defined"),
            next_window_func=None,
            current_window=None
        )
        logout_btn.pack(anchor="ne", padx=10, pady=0)

    # ---------------------------------------------------
    def create_maintenance_box(self):
        self.box_frame.config(bg="white", bd=2, relief="groove")
        self.box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

        # Placeholder label while no data is present
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

        self.placeholder_label.destroy()

        columns = ("Request ID", "Tenant", "Issue", "Date Submitted", "Status")
        self.tree = ttk.Treeview(self.box_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        for row in maintenance:
            self.tree.insert(
                "", "end",
                values=(
                    row[0],  # request_id
                    row[1],  # tenant_name
                    row[2],  # issue
                    row[3],  # created_date
                    row[4],  # status
                )
            )

        self.tree.pack(fill="both", expand=True)

# -------------------------------------------------------
def create_page(parent):
    """Return the frame for this page"""
    return MaintenancePage(parent).frame