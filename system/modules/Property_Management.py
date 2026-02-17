import tkinter as tk
from tkinter import ttk, messagebox

from core.helpers import create_button, create_frame, create_entry, clear_frame
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

    # ---------------------------------------------------
    def create_buttons(self):
        for text, command in [
            ("Add Property", self.on_add_property),
            ("Add City", self.show_add_city_stepper),
            ("Add Building", self.show_add_building_stepper),
        ]:
            create_button(
                self.btns_inner_frame,
                text=text,
                bg="#3B86FF",
                fg="white",
                command=command
            ).pack(side="left", padx=15, pady=10)

    # ---------------------------------------------------
    def refresh_apartments(self):
        clear_frame(self.box_frame)
        apartments = fetch_apartments()

        if not apartments:
            tk.Label(
                self.box_frame,
                text="Registered apartments will appear here",
                font=("Arial", 16),
                bg="white",
                fg="#888"
            ).pack(expand=True, pady=20)
            return

        for apt in apartments:
            text = (
                f"{apt[1]} | {apt[2]} ({apt[3]}) | "
                f"Rooms: {apt[4]} | Type: {apt[5]} | Status: {apt[6]}"
            )
            tk.Label(
                self.box_frame,
                text=text,
                bg="white",
                font=("Arial", 12)
            ).pack(pady=5)

    # ---------------------------------------------------
    def on_add_property(self):
        AddApartmentStepper(self.box_frame, self.refresh_apartments)

    # ===================================================
    # ADD CITY
    # ===================================================
    def show_add_city_stepper(self):
        clear_frame(self.box_frame)

        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(
            container,
            text="Add New City",
            bg="white",
            font=("Arial", 16)
        ).pack(pady=15)

        # Entry wrapped in its own frame
        entry_frame = tk.Frame(container, bg="white")
        entry_frame.pack(pady=5)
        city_entry = create_entry(entry_frame, 0, "", 12)

        def submit_city():
            try:
                create_city(city_entry.get())
                clear_frame(self.box_frame)
                tk.Label(
                    self.box_frame,
                    text="City added successfully!",
                    fg="green",
                    font=("Arial", 14),
                    bg="white"
                ).pack(expand=True)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        create_button(
            container,
            text="Next",
            bg="red",
            fg="white",
            command=submit_city
        ).pack(pady=15)

    # ===================================================
    # ADD BUILDING
    # ===================================================
    def show_add_building_stepper(self):
        clear_frame(self.box_frame)

        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(
            container,
            text="Add New Building",
            bg="white",
            font=("Arial", 16)
        ).pack(pady=10)

        cities = fetch_cities()
        city_map = build_city_map(cities)
        city_names = list(city_map.keys())

        tk.Label(container, text="Select City:", bg="white").pack(pady=5)
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(
            container,
            textvariable=city_var,
            values=city_names,
            state="readonly",
            width=30
        )
        city_dropdown.pack(pady=5)

        street_frame = tk.Frame(container, bg="white")
        street_frame.pack(pady=5)
        street_entry = create_entry(street_frame, 0, "Street:", 12)

        postcode_frame = tk.Frame(container, bg="white")
        postcode_frame.pack(pady=5)
        postcode_entry = create_entry(postcode_frame, 1, "Postcode:", 12)

        def submit_building():
            try:
                city_id = city_map[city_dropdown.get()]
                create_building(city_id, street_entry.get(), postcode_entry.get())
                clear_frame(self.box_frame)
                tk.Label(
                    self.box_frame,
                    text="Building added successfully!",
                    fg="green",
                    font=("Arial", 14),
                    bg="white"
                ).pack(expand=True)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        create_button(
            container,
            text="Next",
            command=submit_building
        ).pack(pady=15)


# =======================================================
# APARTMENT STEPPER
# =======================================================

class AddApartmentStepper:

    TYPES = ['Studio', 'Apartment', 'Penthouse']
    OCCUPANCY = ['Occupied', 'Vacant', 'Unavailable']

    def __init__(self, parent, refresh_callback):
        self.box_frame = parent
        self.refresh_callback = refresh_callback

        cities = fetch_cities()
        buildings = fetch_buildings()

        self.city_map = build_city_map(cities)
        self.city_names = list(self.city_map.keys())
        self.buildings_by_city, self.display_to_id = build_buildings_by_city(buildings)

        self.step_city()

    # ---------------------------------------------------
    def step_city(self):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text="Select City:", bg="white", font=("Arial", 14)).pack(pady=10)
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(
            container,
            textvariable=city_var,
            values=self.city_names,
            state="readonly",
            width=30
        )
        city_dropdown.pack(pady=5)

        create_button(
            container,
            text="Next",
            command=lambda: self.step_address(city_dropdown.get())
        ).pack(pady=15)

    # ---------------------------------------------------
    def step_address(self, selected_city):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text=f"City: {selected_city}", bg="white", font=("Arial", 14)).pack(pady=5)

        city_id = self.city_map[selected_city]
        addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]

        if not addresses:
            tk.Label(container, text="No buildings available.", fg="red", bg="white", font=("Arial", 12)).pack(pady=10)
            create_button(container, text="Back", command=self.step_city).pack(pady=10)
            return

        tk.Label(container, text="Select Address:", bg="white", font=("Arial", 12)).pack(pady=5)
        addr_var = tk.StringVar()
        addr_dropdown = ttk.Combobox(
            container,
            textvariable=addr_var,
            values=addresses,
            state="readonly",
            width=30
        )
        addr_dropdown.pack(pady=5)

        create_button(
            container,
            text="Next",
            command=lambda: self.step_details(selected_city, addr_dropdown.get())
        ).pack(pady=15)

    # ---------------------------------------------------
    def step_details(self, city, address):
        clear_frame(self.box_frame)
        container = tk.Frame(self.box_frame, bg="white")
        container.pack(expand=True)

        tk.Label(container, text=f"City: {city}", bg="white", font=("Arial", 12)).pack(pady=5)
        tk.Label(container, text=f"Address: {address}", bg="white", font=("Arial", 12)).pack(pady=5)

        rooms_frame = tk.Frame(container, bg="white")
        rooms_frame.pack(pady=5)
        rooms_entry = create_entry(rooms_frame, 0, "Rooms:", 12)

        tk.Label(container, text="Type:", bg="white", font=("Arial", 12)).pack(pady=5)
        type_var = tk.StringVar()
        type_dropdown = ttk.Combobox(
            container,
            textvariable=type_var,
            values=self.TYPES,
            state="readonly",
            width=30
        )
        type_dropdown.pack(pady=5)

        tk.Label(container, text="Occupancy:", bg="white", font=("Arial", 12)).pack(pady=5)
        occ_var = tk.StringVar()
        occ_dropdown = ttk.Combobox(
            container,
            textvariable=occ_var,
            values=self.OCCUPANCY,
            state="readonly",
            width=30
        )
        occ_dropdown.pack(pady=5)

        create_button(
            container,
            text="Add Apartment",
            command=lambda: self._submit(
                rooms_entry.get(),
                type_dropdown.get(),
                occ_dropdown.get(),
                city,
                address
            )
        ).pack(pady=15)

    # ---------------------------------------------------
    def _submit(self, rooms, apt_type, occ, city, address):
        building_id = self.display_to_id.get(address)
        city_id = self.city_map[city]
        try:
            create_apartment(city_id, building_id, rooms, apt_type, occ)
            clear_frame(self.box_frame)
            tk.Label(
                self.box_frame,
                text="Apartment added successfully!",
                fg="green",
                font=("Arial", 14),
                bg="white"
            ).pack(expand=True)
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", str(e))


# -------------------------------------------------------
def create_page(parent):
    return ApartmentManagerPage(parent).frame
