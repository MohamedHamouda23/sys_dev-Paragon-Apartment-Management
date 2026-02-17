import tkinter as tk
from tkinter import ttk, messagebox
from core.helpers import create_button, create_frame
from core.database import check_connection 
from core.database import (
    get_all_cities, add_city, get_all_buildings, add_building,
    get_all_apartments, add_apartment,check_connection
)

class ApartmentManagerPage:
    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        self.create_buttons()

    def create_buttons(self):
        add_property_btn = create_button(
            self.btns_inner_frame,
            text="Add Property",
            bg="#3B86FF",
            fg="white",
            command=self.on_add_property
        )
        add_property_btn.pack(side="left", padx=(0, 15), pady=10)

        add_city_btn = create_button(
            self.btns_inner_frame,
            text="Add City",
            bg="#3B86FF",
            fg="white",
            command=self.show_add_city_stepper
        )
        add_city_btn.pack(side="left", padx=(0, 15), pady=10)

        add_building_btn = create_button(
            self.btns_inner_frame,
            text="Add Building",
            bg="#3B86FF",
            fg="white",
            command=self.show_add_building_stepper
        )
        add_building_btn.pack(side="left", padx=(0, 0), pady=10)

    def refresh_apartments(self):
        for widget in self.box_frame.winfo_children():
            widget.destroy()

        apartments = get_all_apartments()

        if not apartments:
            tk.Label(
                self.box_frame,
                text="Registered apartments will appear here",
                font=("Arial", 16),
                bg="white",
                fg="#888"
            ).place(relx=0.5, rely=0.5, anchor="center")
        else:
            for apt in apartments:
                apt_str = f"{apt[1]} | {apt[2]} ({apt[3]}) | Rooms: {apt[4]} | Type: {apt[5]} | Status: {apt[6]}"
                tk.Label(
                    self.box_frame,
                    text=apt_str,
                    anchor="w",
                    bg="white",
                    font=("Arial", 12)
                ).pack(fill="x", padx=10, pady=2)

    # ---------------------- Add Property ----------------------
    def on_add_property(self):
        AddApartmentStepper(self.box_frame, self.refresh_apartments)

    # ---------------------- Add City ----------------------
    def show_add_city_stepper(self):
        for widget in self.box_frame.winfo_children():
            widget.destroy()

        tk.Label(self.box_frame, text="Add New City:").pack(pady=(20, 5))
        city_var = tk.StringVar()
        city_entry = tk.Entry(self.box_frame, textvariable=city_var, width=30)
        city_entry.pack(pady=5)

        def submit_city():
            city_name = city_entry.get().strip()
            if not city_name:
                messagebox.showerror("Error", "City name cannot be empty.")
                return
            try:
                add_city(city_name)
                for widget in self.box_frame.winfo_children():
                    widget.destroy()
                tk.Label(self.box_frame, text="City added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(self.box_frame, text="Add City", command=submit_city).pack(pady=10)

    # ---------------------- Add Building ----------------------
    def show_add_building_stepper(self):
        for widget in self.box_frame.winfo_children():
            widget.destroy()

        tk.Label(self.box_frame, text="Add New Building:").pack(pady=(20, 5))

        cities = get_all_cities()
        city_names = [c[1] for c in cities]
        self.city_ids = {c[1]: c[0] for c in cities}

        tk.Label(self.box_frame, text="Select City:").pack()
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(self.box_frame, textvariable=city_var, values=city_names, state="readonly")
        city_dropdown.pack()

        tk.Label(self.box_frame, text="Street Address:").pack()
        street_var = tk.StringVar()
        street_entry = tk.Entry(self.box_frame, textvariable=street_var, width=40)
        street_entry.pack()

        tk.Label(self.box_frame, text="Postcode:").pack()
        postcode_var = tk.StringVar()
        postcode_entry = tk.Entry(self.box_frame, textvariable=postcode_var, width=20)
        postcode_entry.pack()

        def submit_building():
            city = city_dropdown.get()
            street = street_entry.get().strip()
            postcode = postcode_entry.get().strip()
            if not (city and street and postcode):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                city_id = self.city_ids[city]
                add_building(city_id, street, postcode)
                for widget in self.box_frame.winfo_children():
                    widget.destroy()
                tk.Label(self.box_frame, text="Building added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(self.box_frame, text="Add Building", command=submit_building).pack(pady=10)

    # ---------------------- Label Wrapping ----------------------
    def wrap_labels(self):
        def update_wrap(event):
            for widget in self.box_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(wraplength=self.box_frame.winfo_width() - 40, justify="left")
        self.box_frame.bind("<Configure>", update_wrap)



# ---------------------- Apartment Stepper Class ----------------------

class AddApartmentStepper:
    def __init__(self, parent, refresh_callback):
        self.box_frame = parent
        self.refresh_callback = refresh_callback
        self.city_ids = {}
        self.buildings_by_city = {}
        self.display_to_id = {}
        self.types = ['Studio', 'Apartment', 'Penthouse']
        self.occupancy = ['Occupied', 'Vacant', 'Unavailable']

        self.load_data()
        self.step_city()

    # -------------------- Load Data --------------------
    def load_data(self):
        # Load cities
        cities = get_all_cities()
        self.city_ids = {name: c_id for c_id, name in cities}
        self.city_names = [name for _, name in cities]

        # Load buildings
        buildings = get_all_buildings()
        for b_id, c_id, street, postcode in buildings:
            display = f"{street} ({postcode})"
            self.buildings_by_city.setdefault(c_id, []).append((b_id, display))
            self.display_to_id[display] = b_id

    # -------------------- Step 1: Select City --------------------
    def step_city(self):
        self.clear_frame()
        tk.Label(self.box_frame, text="Select City:").pack()
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(self.box_frame, textvariable=city_var, values=self.city_names, state="readonly")
        city_dropdown.pack()
        tk.Button(self.box_frame, text="Next", command=lambda: self.step_address(city_dropdown.get())).pack(pady=10)

    # -------------------- Step 2: Select Address --------------------
    def step_address(self, selected_city):
        self.clear_frame()
        tk.Label(self.box_frame, text=f"City: {selected_city}").pack()
        tk.Label(self.box_frame, text="Select Address:").pack()

        city_id = self.city_ids[selected_city]
        addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]

        if not addresses:
            tk.Label(self.box_frame, text="No buildings available in this city.", fg="red", font=("Arial", 12)).pack(pady=10)
            tk.Button(self.box_frame, text="Back", command=self.step_city).pack(pady=10)
            return

        address_var = tk.StringVar()
        address_dropdown = ttk.Combobox(self.box_frame, textvariable=address_var, values=addresses, state="readonly", width=40)
        address_dropdown.pack()
        tk.Button(self.box_frame, text="Next", command=lambda: self.step_details(selected_city, address_dropdown.get())).pack(pady=10)

    # -------------------- Step 3: Enter Apartment Details --------------------
    def step_details(self, selected_city, selected_address):
        self.clear_frame()
        tk.Label(self.box_frame, text=f"City: {selected_city}").pack()
        tk.Label(self.box_frame, text=f"Address: {selected_address}").pack()

        tk.Label(self.box_frame, text="Number of Rooms:").pack()
        rooms_entry = tk.Entry(self.box_frame)
        rooms_entry.pack()

        tk.Label(self.box_frame, text="Type:").pack()
        type_var = tk.StringVar()
        type_dropdown = ttk.Combobox(self.box_frame, textvariable=type_var, values=self.types, state="readonly")
        type_dropdown.pack()

        tk.Label(self.box_frame, text="Occupancy:").pack()
        occ_var = tk.StringVar()
        occ_dropdown = ttk.Combobox(self.box_frame, textvariable=occ_var, values=self.occupancy, state="readonly")
        occ_dropdown.pack()

        tk.Button(
            self.box_frame,
            text="Add Apartment",
            command=lambda: self.submit(
                rooms_entry.get(),
                type_dropdown.get(),
                occ_dropdown.get(),
                selected_city,
                selected_address
            )
        ).pack(pady=10)

    # -------------------- Submit Apartment --------------------
    def submit(self, num_rooms, apt_type, occ, selected_city, selected_address):
        if not (num_rooms and apt_type and occ):
            messagebox.showerror("Error", "All fields are required.")
            return

        building_id = self.display_to_id.get(selected_address)
        city_id = self.city_ids[selected_city]

        if building_id is None:
            messagebox.showerror("Error", "Invalid building selection.")
            return

        try:
            add_apartment(city_id, building_id, int(num_rooms), apt_type, occ)
            self.clear_frame()
            tk.Label(self.box_frame, text="Apartment added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------- Utility --------------------
    def clear_frame(self):
        for widget in self.box_frame.winfo_children():
            widget.destroy()



def create_page(parent):
    page = ApartmentManagerPage(parent)
    return page.frame
