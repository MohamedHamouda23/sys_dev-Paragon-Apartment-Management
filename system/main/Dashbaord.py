# ============================================================================
# DASHBOARD
# Main dashboard with role-based page access
# ============================================================================

from main.helpers import create_side_navbar

import tkinter as tk
from tkinter import ttk
from modules import User_Management, Property_Management, Tenant_Management, Payments_Management, complaints
from modules import Lease_Management, Report_Management, Lifecycle_Management, Request_Management


def page_template(main_window, user_info): 
    """Create main dashboard window with role-based navigation"""
    
    # Create main window
    root = tk.Tk()
    root.title("Dashboard")
    root.geometry("900x900")  
    root.minsize(1000, 800)    
    root.configure(bg='#c9e4c4')

    # Create content area
    content_frame = tk.Frame(root, bg='#c9e4c4')
    content_frame.pack(fill="both", expand=True, side="right")

    # Initialize page storage
    pages = {}

    # Define all available pages
    ALL_PAGES = {
        "Users": User_Management,
        "Properties": Property_Management,
        "Tenants": Tenant_Management,
        "Leases": Lease_Management,
        "Reports": Report_Management,
        "Maintenance": Request_Management,
        "Request Lifecycle": Lifecycle_Management,
        "Payments": Payments_Management,
        "Payment": Payments_Management,
        "complaints": complaints,
    }

    # Get user role
    role = user_info[4]

    # Define pages accessible by each role
    ROLE_PAGES = {
        "Administrators": [
            "Users", "Properties", "Tenants",
            "Leases", "Reports", "Maintenance"
        ],
        "Front-desk Staff": [
            "Tenants", "Leases", "Maintenance"
        ],
        "Maintenance Staff": [
            "Maintenance", "Request Lifecycle"
        ],
        "Manager": [
            "Properties", "Tenants",
            "Leases", "Reports", "Maintenance"
        ],
        "Finance Manager": [
            "Reports", "Payments"
        ],
        "Tenant": [
            "Payment"
        ]
    }

    # Get pages allowed for current role
    allowed_pages = ROLE_PAGES.get(role, [])

    # Filter available modules by allowed pages
    page_modules = {
        name: ALL_PAGES[name]
        for name in allowed_pages
        if name in ALL_PAGES
    }

    # Create all page frames
    for name, module in page_modules.items():
        if name in ("Users", "Properties", "Payment", "Payments"):
            # Users page needs user_info parameter
            frame = module.create_page(content_frame, user_info=user_info)
        else:
            # Other pages don't need user_info in create_page
            frame = module.create_page(content_frame)
        frame.place(relwidth=1, relheight=1)
        pages[name] = frame

    # Universal refresh function for all pages
    def refresh_page(page_name, frame):
        """Universal refresh method that works for any page"""
        try:
            # Method 1: Check for on_show method (preferred)
            if hasattr(frame, 'on_show'):
                frame.on_show()
                
            # Method 2: Check for common refresh methods
            elif hasattr(frame, 'refresh_data'):
                frame.refresh_data()
            elif hasattr(frame, 'refresh'):
                frame.refresh()
            elif hasattr(frame, 'update_data'):
                frame.update_data()
            elif hasattr(frame, 'load_data'):
                frame.load_data()
            
            # Method 3: For pages with a render method
            elif hasattr(frame, '_render'):
                # Clear and re-render
                for widget in frame.winfo_children():
                    widget.destroy()
                frame._render()
            
            # Method 4: For pages that are just frames with data tables
            else:
                # Try to find and refresh any treeviews or data displays
                refreshed = False
                for child in frame.winfo_children():
                    if isinstance(child, ttk.Treeview):
                        # Try to find a method to reload data
                        if hasattr(frame, 'load_data_into_tree'):
                            frame.load_data_into_tree()
                            refreshed = True
                            break
                        elif hasattr(frame, '_load_requests'):
                            frame._load_requests()
                            refreshed = True
                            break
                        elif hasattr(frame, '_load_data'):
                            frame._load_data()
                            refreshed = True
                            break
                

                    
        except Exception as e:
            print(f"Warning: Could not refresh page '{page_name}': {e}")

    # Page switching function with universal refresh
    def show_page(page_name):
        """Bring selected page to front and refresh its content"""
        frame = pages.get(page_name)
        if frame:
            # Refresh the page using universal method
            refresh_page(page_name, frame)
            
            # Bring the frame to front
            frame.tkraise()

    # Create button commands for navigation
    button_commands = [
        lambda n=name: show_page(n)
        for name in page_modules
    ]

    # Create side navigation bar
    create_side_navbar(
        parent=root,
        button_text=list(page_modules.keys()),
        user_info=user_info,
        button_command=button_commands
    )

    # Show first page by default
    if page_modules:
        first_page = list(page_modules.keys())[0]
        show_page(first_page)

    # Start main loop
    root.mainloop()