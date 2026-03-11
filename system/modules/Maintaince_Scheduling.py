import tkinter as tk
from tkinter import ttk


class TasksAndTenantPage:


    def __init__(self, parent, user_info=None):
        self.parent    = parent
        self.user_info = user_info
        self.frame     = tk.Frame(parent, bg="white")
        self._build()

    def _build(self):
        tk.Label(
            self.frame,
            text="Tasks & Tenant Interaction",
            font=("Arial", 14, "bold"),
            bg="white",
        ).pack(anchor="w", padx=16, pady=(12, 6))


        tk.Label(
            self.frame,
            text="(Scheduling and tenant interaction features — not yet implemented)",
            bg="white", fg="grey", font=("Arial", 10, "italic"),
        ).pack(expand=True, pady=40)



def create_page(parent, user_info=None):
    return TasksAndTenantPage(parent, user_info=user_info).frame