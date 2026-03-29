# ============================================================================
# DASHBOARD - MAC-SAFE TRUE FULLSCREEN & RESIZE PROTECTION
# ============================================================================

import tkinter as tk
from tkinter import ttk
import os
import sys
from main.helpers import create_side_navbar
from modules import (
    User_Management, Property_Management, Tenant_Management,
    Payments_Management, complaints, Lease_Management,
    Report_Management, Lifecycle_Management, Request_Management
)

def page_template(main_window, user_info):
    root = tk.Tk()
    root.title("Property Management Dashboard")
    root.configure(bg="#c9e4c4")

    # --- WINDOW SIZE & CONSTRAINTS ---
    # Prevents the user from shrinking the window until buttons disappear
    root.minsize(1024, 768)

    def center_window(window, w, h):
        """Centers the window on the screen when exiting fullscreen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (w // 2)
        y = (screen_height // 2) - (h // 2)
        window.geometry(f'{w}x{h}+{x}+{y}')

    def enable_fullscreen():
        root.attributes("-fullscreen", True)

    def toggle_fullscreen(event=None):
        state = not root.attributes("-fullscreen")
        root.attributes("-fullscreen", state)
        if not state:
            center_window(root, 1280, 800)
        return "break"

    def exit_fullscreen(event=None):
        root.attributes("-fullscreen", False)
        center_window(root, 1280, 800)
        return "break"

    # Initialization for Mac/Windows
    if sys.platform == "darwin":
        root.wait_visibility()
        root.after(100, enable_fullscreen)
    else:
        root.attributes("-fullscreen", True)

    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", exit_fullscreen)

    # --- LAYOUT ---
    content_frame = tk.Frame(root, bg="#c9e4c4")
    content_frame.pack(fill="both", expand=True, side="right")

    pages = {}
    import main.Maintenance_page as MaintenancePage

    ALL_PAGES = {
        "Users": User_Management,
        "Properties": Property_Management,
        "Tenants": Tenant_Management,
        "Reports": Report_Management,
        "Maintenance": MaintenancePage,
        "Request Lifecycle": Lifecycle_Management,
        "Payments": Payments_Management,
        "complaints": complaints,
        "Lease": Lease_Management,
        "Profile": Tenant_Management,
    }

    role = user_info[4]
    ROLE_PAGES = {
        "Administrators": ["Users", "Properties", "Lease", "Reports", "Request Lifecycle"],
        "Front-desk Staff": ["Tenants", "Lease", "Maintenance","complaints"],
        "Maintenance Staff": ["Request Lifecycle", "Reports"],
        "Manager": ["Properties", "Lease", "Reports", "Maintenance", "Request Lifecycle"],
        "Finance Manager": ["Reports", "Payments"],
        "Tenant": ["Profile", "Payments", "Maintenance","Request Lifecycle" , "Complaints", "Lease","Reports"],
    }

    allowed_pages = ROLE_PAGES.get(role, [])
    page_modules = {name: ALL_PAGES[name] for name in allowed_pages if name in ALL_PAGES}

    for name, module in page_modules.items():
        # Consistent page creation
        frame = module.create_page(content_frame, user_info=user_info)
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        pages[name] = frame

    def show_page(page_name):
        frame = pages.get(page_name)
        if frame:
            # Trigger refresh if the module supports it
            for m in ["on_show", "refresh_payments", "refresh_data"]:
                if hasattr(frame, m):
                    getattr(frame, m)()
                    break
            frame.tkraise()

    button_commands = [lambda n=name: show_page(n) for name in page_modules]

    create_side_navbar(
        parent=root,
        button_text=list(page_modules.keys()),
        user_info=user_info,
        button_command=button_commands,
    )

    if page_modules:
        show_page(list(page_modules.keys())[0])

    root.mainloop()

