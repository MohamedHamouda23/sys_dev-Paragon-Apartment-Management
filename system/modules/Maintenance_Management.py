import tkinter as tk
from tkinter import ttk, messagebox

from database.maintaince_service import get_all_requests, viewFull
from main.helpers import create_button, create_frame


# -------------------------------------------------------
class MaintenancePage:
    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        self.is_detail_view = False

        self.create_buttons()
        self.create_maintenance_box()

        self.populate_maintenance_requests()

    # ---------------------------------------------------
    def create_buttons(self):

        # Wrapper frame to hold button + swap its label
        self.toggle_btn_frame = create_button(
            self.btns_inner_frame,
            text="View Details",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=self.toggle_view
        )
        
        self.toggle_btn_frame.pack(side="left", padx=15, pady=50)

        # Find the label inside the custom button so we can update its text
        self.toggle_btn_label = None
        for widget in self.toggle_btn_frame.winfo_children():
            if isinstance(widget, tk.Label):
                self.toggle_btn_label = widget
                break

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
    def _set_toggle_text(self, text):
        """Update the toggle button label text safely."""
        if self.toggle_btn_label:
            self.toggle_btn_label.config(text=text)

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

        labels = ("Request ID", "Issue", "Description", "Priority", "Date Submitted",
                  "Resolved Date", "Status", "Notes", "Tenant", "Apt Type",
                  "Postcode", "Staff", "Assigned Date", "Is Current")

        self.tree.pack_forget()

        if hasattr(self, "detail_frame"):
            self.detail_frame.destroy()

        self.detail_frame = tk.Frame(self.box_frame, bg="white")
        self.detail_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for i, (label, value) in enumerate(zip(labels, full_data)):
            tk.Label(self.detail_frame, text=f"{label}:", font=("Arial", 10, "bold"), bg="white").grid(row=i, column=0, sticky="w", padx=10, pady=3)
            tk.Label(self.detail_frame, text=value, bg="white").grid(row=i, column=1, sticky="w", padx=10, pady=3)

        self.is_detail_view = True
        self._set_toggle_text("View All")

    # ---------------------------------------------------
    def view_all(self):
        self.populate_maintenance_requests()
        self.is_detail_view = False
        self._set_toggle_text("View All")

    # ---------------------------------------------------
    def toggle_view(self):
        if self.is_detail_view:
            self.view_all()
        else:
            self.view_details()


# -------------------------------------------------------
def create_page(parent):
    return MaintenancePage(parent).frame