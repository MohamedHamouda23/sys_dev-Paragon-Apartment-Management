import tkinter as tk
from tkinter import ttk, messagebox
from core.helpers import create_button, create_frame, clear_frame
from core.property_service import (
    fetch_cities, fetch_buildings, fetch_apartments,
    create_city, create_building, create_apartment,
    build_city_map, build_buildings_by_city
)

class ApartmentManagerPage:
    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        
        self.create_buttons()
        self.refresh_apartments()

    def create_buttons(self):
        for text, command in [
            ("Add Property", self.on_add_property),
            ("Add City",     self.show_add_city_stepper),
            ("Add Building", self.show_add_building_stepper),
        ]:
            create_button(
                self.btns_inner_frame, text=text,
                bg="#3B86FF", fg="white", command=command
            ).pack(side="left", padx=(0, 15), pady=10)

    def refresh_apartments(self):
        clear_frame(self.box_frame)
        apartments = fetch_apartments()
        if not apartments:
            tk.Label(
                self.box_frame,
                text="Registered apartments will appear here",
                font=("Arial", 16), bg="white", fg="#888"
            ).pack(expand=True)
        else:
            for apt in apartments:
                text = f"{apt[1]} | {apt[2]} ({apt[3]}) | Rooms: {apt[4]} | Type: {apt[5]} | Status: {apt[6]}"
                tk.Label(
                    self.box_frame, text=text,
                    bg="white", font=("Arial", 12)
                ).pack(pady=2)

    def on_add_property(self):
        AddApartmentStepper(self.box_frame, self.refresh_apartments)

    def show_add_city_stepper(self):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text="Add New City:", bg="white", font=("Arial", 14)).pack(pady=5)
        city_var = tk.StringVar()
        city_entry = tk.Entry(container, textvariable=city_var, width=30)
        city_entry.pack(pady=5)

        def submit_city():
            try:
                create_city(city_entry.get())
                clear_frame(self.box_frame)
                tk.Label(self.box_frame, text="City added successfully!", fg="green", font=("Arial", 14)).pack(expand=True)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(container, text="Add City", command=submit_city).pack(pady=10)

    def show_add_building_stepper(self):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text="Add New Building:", bg="white", font=("Arial", 14)).pack(pady=5)

        cities = fetch_cities()
        city_map = build_city_map(cities)
        city_names = list(city_map.keys())

        tk.Label(container, text="Select City:", bg="white").pack(pady=2)
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(container, textvariable=city_var, values=city_names, state="readonly")
        city_dropdown.pack(pady=2)

        tk.Label(container, text="Street Address:", bg="white").pack(pady=2)
        street_entry = tk.Entry(container, width=40)
        street_entry.pack(pady=2)

        tk.Label(container, text="Postcode:", bg="white").pack(pady=2)
        postcode_entry = tk.Entry(container, width=20)
        postcode_entry.pack(pady=2)

        def submit_building():
            try:
                city_id = city_map[city_dropdown.get()]
                create_building(city_id, street_entry.get(), postcode_entry.get())
                clear_frame(self.box_frame)
                tk.Label(self.box_frame, text="Building added successfully!", fg="green", font=("Arial", 14)).pack(expand=True)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(container, text="Add Building", command=submit_building).pack(pady=10)


class AddApartmentStepper:
    TYPES     = ['Studio', 'Apartment', 'Penthouse']
    OCCUPANCY = ['Occupied', 'Vacant', 'Unavailable']

    def __init__(self, parent, refresh_callback):
        self.box_frame        = parent
        self.refresh_callback = refresh_callback

        cities    = fetch_cities()
        buildings = fetch_buildings()

        self.city_map           = build_city_map(cities)
        self.city_names         = list(self.city_map.keys())
        self.buildings_by_city, self.display_to_id = build_buildings_by_city(buildings)

        self.step_city()

    def step_city(self):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text="Select City:", bg="white").pack(pady=5)
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(container, textvariable=city_var, values=self.city_names, state="readonly")
        city_dropdown.pack(pady=5)
        tk.Button(container, text="Next",
                  command=lambda: self.step_address(city_dropdown.get())).pack(pady=10)

    def step_address(self, selected_city):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text=f"City: {selected_city}", bg="white", font=("Arial", 12)).pack(pady=5)

        city_id   = self.city_map[selected_city]
        addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]

        if not addresses:
            tk.Label(container, text="No buildings available in this city.", fg="red", bg="white").pack(pady=10)
            tk.Button(container, text="Back", command=self.step_city).pack(pady=10)
            return

        tk.Label(container, text="Select Address:", bg="white").pack(pady=2)
        address_var = tk.StringVar()
        address_dropdown = ttk.Combobox(container, textvariable=address_var, values=addresses, state="readonly", width=40)
        address_dropdown.pack(pady=2)
        tk.Button(container, text="Next",
                  command=lambda: self.step_details(selected_city, address_dropdown.get())).pack(pady=10)

    def step_details(self, selected_city, selected_address):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text=f"City: {selected_city}", bg="white").pack(pady=2)
        tk.Label(container, text=f"Address: {selected_address}", bg="white").pack(pady=2)

        tk.Label(container, text="Number of Rooms:", bg="white").pack(pady=2)
        rooms_entry = tk.Entry(container)
        rooms_entry.pack(pady=2)

        tk.Label(container, text="Type:", bg="white").pack(pady=2)
        type_var = tk.StringVar()
        type_dropdown = ttk.Combobox(container, textvariable=type_var, values=self.TYPES, state="readonly")
        type_dropdown.pack(pady=2)

        tk.Label(container, text="Occupancy:", bg="white").pack(pady=2)
        occ_var = tk.StringVar()
        occ_dropdown = ttk.Combobox(container, textvariable=occ_var, values=self.OCCUPANCY, state="readonly")
        occ_dropdown.pack(pady=2)

        tk.Button(
            container, text="Add Apartment",
            command=lambda: self._submit(
                rooms_entry.get(), type_dropdown.get(),
                occ_dropdown.get(), selected_city, selected_address
            )
        ).pack(pady=10)

    def _submit(self, num_rooms, apt_type, occ, selected_city, selected_address):
        building_id = self.display_to_id.get(selected_address)
        city_id     = self.city_map[selected_city]
        try:
            create_apartment(city_id, building_id, num_rooms, apt_type, occ)
            clear_frame(self.box_frame)
            tk.Label(self.box_frame, text="Apartment added successfully!", fg="green", font=("Arial", 14)).pack(expand=True)
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", str(e))


def create_page(parent):
    return ApartmentManagerPage(parent).frame
