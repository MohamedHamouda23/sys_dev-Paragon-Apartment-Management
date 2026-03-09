import tkinter as tk
from main.helpers import create_button
from tkinter import messagebox

#-- core imports for shared ui helpers
from main.helpers import (
    create_button, create_frame, clear_frame, styled_label, form_field, form_dropdown, card, BG, ACCENT, FONT_TITLE, FONT_LABEL 
)



class TenantManagerPage: #initialise tenant managment page
    def __init__(self, parent):
        self.parent=parent 
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent) #gives standard 3 section layout
        self.box_frame.pack_propagate(False)

        self.tenants=[ #temporary dummy data until data base integration
            {"Name":"emily jones", "Email": "em.jones@gmail.com", "Phone Number": "07635244267", "Occupation":"retail", 
             "Reference Name":"Mark Hudson", "Reference Email":"mark.hudson@icloud.com", 
             "Apartment Requirements": "1 Bedroom", "National Insurance Number":"QQ123456A","Lease Period":"36 months" }
        ]

        self.create_buttons() #builds top buttons
        self.show_home() #loads tenant "home" page

    #---------------------------

    def create_buttons(self): #creates top button bar using create_button from helpers.py
        for text, command in [
            ("View Tenant Info", self.view_tenant_info),
            ("Add Tenant", self.add_tenant),
            ("View Complaints", self.complaints),
        ]:
            create_button(
                self.btns_inner_frame,
                text=text,
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=command
            ).pack(side="left", padx=15, pady=50)

    #---------------------------

    def clear_box(self):
        clear_frame(self.box_frame)

    #---------------------------

    def show_home(self):
        self.clear_box()

        container = card(self.box_frame)
        container.config(width=600, height=150)

        styled_label(container, "Tenant Management", font=FONT_TITLE, fg="#222").pack(pady=10)

    #--------------------------------

    def view_tenant_info(self):
        self.clear_box()

        container = card(self.box_frame)
        container.config(width=900, height=500)

        styled_label(container, "Tenant Info", font=FONT_TITLE, fg="#222").pack(pady=10)

        columns_frame = tk.Frame(container, bg="white")
        columns_frame.pack(pady=10)

        floors = {
            "Floor 1": ["A1","A2","A3","A4","A5","A6","A7","A8"],
            "Floor 2": ["A9","A10","A11","A12","A13","A14","A15","A16"],
            "Floor 3": ["A17","A18","A19","A20"],
            "Floor 4": ["A21","A22","A23","A24"]
        }

        col_index = 0
        for floor_name, apartments in floors.items():
            col = tk.Frame(columns_frame, bg="white")
            col.grid(row=0, column=col_index, padx=25)

            styled_label(col, floor_name, fg="#333", font=FONT_LABEL).pack(pady=(0, 5))

            for apt in apartments:
                styled_label(col, f"{apt} - (empty)", fg="#555").pack(anchor="w")

            col_index += 1

    #---------------------------------

    def refresh_tenants(self): #main tenant list view
        self.clear_box()
        container = card(self.box_frame)
        container.config(width=900, height=500)

        if not self.tenants:
            styled_label(container, "No tenants found", fg="#888").pack(pady=20)
            return
        
        for t in self.tenants:
            text=f"{t['Name']} | {t['Email']} | {t['Phone Number']} | {t['Occupation']} | {t['Reference Name']} | {t['Reference Email']} | {t['Apartment Requirements']} | {t['National Insurance Number']} | {t['Lease Period']}"
            styled_label(container, text, fg="#333").pack(pady=5, anchor="w")

    #-----------------------------------
    def add_tenant(self):
        self.clear_box()

        # MUCH bigger card
        container = card(self.box_frame)
        container.config(width=950, height=550)

        styled_label(container, "Add New Tenant", font=FONT_TITLE, fg="#222").pack(pady=(0,4))
        tk.Frame(container, bg=ACCENT, height=3, width=80).pack(pady=(0,16))

        # 3-column layout for form fields
        form_frame = tk.Frame(container, bg="white")
        form_frame.pack(pady=10)

        # column frames
        col1 = tk.Frame(form_frame, bg="white")
        col2 = tk.Frame(form_frame, bg="white")
        col3 = tk.Frame(form_frame, bg="white")

        col1.grid(row=0, column=0, padx=25)
        col2.grid(row=0, column=1, padx=25)
        col3.grid(row=0, column=2, padx=25)

        # form fields
        first_name = form_field(col1, "First Name")
        surname = form_field(col1, "Surname")
        email = form_field(col1, "Email")

        phone_number = form_field(col2, "Phone Number")
        occupation = form_field(col2, "Occupation")
        reference_name = form_field(col2, "Reference Name")

        reference_email = form_field(col3, "Reference Email")
        apartment_requirments = form_field(col3, "Apartment Requirements")
        national_insurance_number = form_field(col3, "National Insurance Number")
        lease_period = form_field(col3, "Lease Period")

        #submit handler
        def submit():
            full_name=f"{first_name.get()} {surname.get()}"
            self.tenants.append({
                "Name": full_name,
                "Email": email.get(),
                "Phone Number": phone_number.get(),
                "Occupation": occupation.get(),
                "Reference Name": reference_name.get(), 
                "Reference Email": reference_email.get(), 
                "Apartment Requirements": apartment_requirments.get(), 
                "National Insurance Number": national_insurance_number.get(), 
                "Lease Period": lease_period.get()
            })

            self.clear_box()
            styled_label(self.box_frame, "Tenant added successfully", fg="#2E7D32").pack(expand=True)
            self.box_frame.after(1200, self.refresh_tenants)

        # submit button
        create_button(
            container,
            text="Create Tenant",
            width=200,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=submit
        ).pack(pady=20)

    #----------------------------------------
            
    def complaints(self):
        self.clear_box()
        container = card(self.box_frame)
        container.config(width=900, height=500)

        styled_label(container,"Tenant Complaints", font=FONT_TITLE,fg="#222").pack(pady=10)
        styled_label(container,"No complaints",fg="#888").pack(pady=20)

#--------------------------------------            

def create_page(parent):
    return TenantManagerPage(parent).frame
