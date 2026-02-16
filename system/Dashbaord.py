from helpers import create_side_navbar
import tkinter as tk
import User_Management, Property_Management, Tenant_Management, Lease_Management, Report_Management, Maintenance_Management




def page_template(main_window,user_info): 
    root = tk.Tk()
    root.title("Dashboard")
    root.geometry("850x650")
    root.minsize(850, 650)
    root.configure(bg='#c9e4c4')

    content_frame = tk.Frame(root, bg='#c9e4c4')
    content_frame.pack(fill="both", expand=True, side="right")

    pages = {}

    page_modules = {
        "Users": User_Management,
        "Properties": Property_Management,
        "Tenants": Tenant_Management,
        "Leases": Lease_Management,
        "Reports": Report_Management,
        "Maintenance": Maintenance_Management
    }



    for name, module in page_modules.items():
        frame = module.create_page(content_frame)
        frame.place(relwidth=1, relheight=1)
        pages[name] = frame



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
    
    def show_page(page_name):
        frame = pages.get(page_name)
        if frame:
            frame.tkraise()

    show_page("Users")  

    root.mainloop()


