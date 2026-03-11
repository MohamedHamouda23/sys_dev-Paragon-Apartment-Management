from main.helpers import create_side_navbar   # absolute import

import tkinter as tk
from modules import User_Management, Property_Management, Tenant_Management,Payments_Management,complaints
from modules import Lease_Management, Report_Management, Maintenance_Management,Maintaince_Scheduling,Request_Lifecycle

def page_template(main_window, user_info): 
    root = tk.Tk()
    root.title("Dashboard")
    root.geometry("850x650")
    root.minsize(850, 650)
    root.configure(bg='#c9e4c4')

    content_frame = tk.Frame(root, bg='#c9e4c4')
    content_frame.pack(fill="both", expand=True, side="right")

    pages = {}

    ALL_PAGES = {
        "Users": User_Management,
        "Properties": Property_Management,
        "Tenants": Tenant_Management,
        "Leases": Lease_Management,
        "Reports": Report_Management,
        "Maintenance": Maintenance_Management,
        "Request Lifecycle": Request_Lifecycle,
        "Maintaince Scheduling": Maintaince_Scheduling,
        "Payments": Payments_Management,
        "complaints": complaints,
    }

    role = user_info[4]

    ROLE_PAGES = {
        "Administrators": [
            "Users", "Properties", "Tenants",
            "Leases", "Reports", "Maintenance"
        ],
        "Front-desk Staff": [
            "Tenants", "Leases", "Maintenance"
        ],
        "Maintenance Staff": [
            "Maintenance", "Request Lifecycle","Maintaince Scheduling"
        ],
        "Manager": [
            "Properties", "Tenants",
            "Leases", "Reports", "Maintenance"
        ],
        "Finance Manager": [
            "Reports", "Payments"
        ]
    }

    allowed_pages = ROLE_PAGES.get(role, [])

    page_modules = {
        name: ALL_PAGES[name]
        for name in allowed_pages
        if name in ALL_PAGES
    }

    for name, module in page_modules.items():
        if name == "Users":
            frame = module.create_page(content_frame, user_info=user_info)
        else:
            frame = module.create_page(content_frame)
        frame.place(relwidth=1, relheight=1)
        pages[name] = frame

    def show_page(page_name):
        frame = pages.get(page_name)
        if frame:
            frame.tkraise()

    button_commands = [
        lambda n=name: show_page(n)
        for name in page_modules
    ]

    create_side_navbar(
        parent=root,
        button_text=list(page_modules.keys()),
        user_info=user_info,
        button_command=button_commands
    )

    if page_modules:
        first_page = list(page_modules.keys())[0]
        show_page(first_page)

    root.mainloop()