import tkinter as tk
from tkinter import ttk, messagebox

from core.helpers import (
    create_button, create_frame, clear_frame,
    styled_label, styled_entry, styled_dropdown,
    form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE, FONT_LABEL
)

from core.property_service import (
    fetch_cities, fetch_buildings, fetch_apartments,
    create_city, create_building, create_apartment,
    build_city_map, build_buildings_by_city
)



# -------------------------------------------------------

class ApartmentManagerPage:

    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        self.create_buttons()
        self.refresh_apartments()

    # ---------------------------------------------------
    def create_buttons(self):
        for text, command in [
            ("Add Property",  self.on_add_property),
            ("Add City",      self.show_add_city_stepper),
            ("Add Building",  self.show_add_building_stepper),
        ]:
            create_button(
                self.btns_inner_frame,
                text=text,
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=command,
                next_window_func=None,
                current_window=None
            ).pack(side="left", padx=15, pady=50)


        logout_btn = create_button(
            self.btns_inner_frame,  # or self.frame if you want it at top-right of whole page
            text="➜]",
            width=35,
            height=35,
            bg="#FF3B3B",
            fg="white",
            command=lambda: logout_page(self.frame, self.parent, Log_window),
            next_window_func=None,
            current_window=None
        )
        logout_btn.pack(anchor="ne", padx=10, pady=0)  # top-right corner
            

    # ---------------------------------------------------
    def refresh_apartments(self):
        clear_frame(self.box_frame)
        apartments = fetch_apartments()

        container = card(self.box_frame)

        if not apartments:
            styled_label(
                container,
                "Registered apartments will appear here",
                font=FONT_LABEL,
                fg="#888"
            ).pack(expand=True, pady=20)
            return

        for apt in apartments:
            text = (
                f"{apt[1]} | {apt[2]} ({apt[3]}) | "
                f"Rooms: {apt[4]} | Type: {apt[5]} | Status: {apt[6]}"
            )
            styled_label(container, text, fg="#333").pack(pady=5, anchor="w")

    # ---------------------------------------------------
    def on_add_property(self):
        AddApartmentStepper(self.box_frame, self.refresh_apartments)

    # ===================================================
    # ADD CITY
    # ===================================================
    def show_add_city_stepper(self):
        clear_frame(self.box_frame)

        container = card(self.box_frame)

        styled_label(container, "Add New City", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))

        city_entry = form_field(container, "City Name", [0])

        def submit_city():
            try:
                create_city(city_entry.get())
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    "✓  City added successfully!",
                    fg="#2E7D32"
                ).pack(expand=True)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=submit_city,
            next_window_func=None,
            current_window=None
        ).pack()

    # ===================================================
    # ADD BUILDING
    # ===================================================
    def show_add_building_stepper(self):
        clear_frame(self.box_frame)

        container = card(self.box_frame)

        styled_label(container, "Add New Building", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))

        cities     = fetch_cities()
        city_map   = build_city_map(cities)
        city_names = list(city_map.keys())

        city_cb        = form_dropdown(container, "Select City", city_names)
        street_entry   = form_field(container, "Street", [0])
        postcode_entry = form_field(container, "Postcode", [0])

        def submit_building():
            try:
                city_id = city_map[city_cb.get()]
                create_building(city_id, street_entry.get(), postcode_entry.get())
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    "✓  Building added successfully!",
                    fg="#2E7D32"
                ).pack(expand=True)
                self.box_frame.after(1200, self.refresh_apartments)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=submit_building,
            next_window_func=None,
            current_window=None
        ).pack()


# =======================================================
# APARTMENT STEPPER
# =======================================================

class AddApartmentStepper:

    TYPES     = ['Studio', 'Apartment', 'Penthouse']
    OCCUPANCY = ['Occupied', 'Vacant', 'Unavailable']

    def __init__(self, parent, refresh_callback):
        self.box_frame        = parent
        self.refresh_callback = refresh_callback

        cities    = fetch_cities()
        buildings = fetch_buildings()

        self.city_map          = build_city_map(cities)
        self.city_names        = list(self.city_map.keys())
        self.buildings_by_city, self.display_to_id = build_buildings_by_city(buildings)

        self.step_city()

    # ---------------------------------------------------
    def step_city(self):
        clear_frame(self.box_frame)

        container = card(self.box_frame)

        styled_label(container, "Add Apartment", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 3 — Select City", fg="#888").pack(pady=(0, 8))

        city_cb = form_dropdown(container, "City", self.city_names)

        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: self.step_address(city_cb.get()),
            next_window_func=None,
            current_window=None
        ).pack()

    # ---------------------------------------------------
    def step_address(self, selected_city):
        clear_frame(self.box_frame)

        container = card(self.box_frame)

        styled_label(container, "Add Apartment", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 3 — Select Address", fg="#888").pack(pady=(0, 8))
        styled_label(container, f"City: {selected_city}", fg="#555").pack(anchor="w")

        city_id   = self.city_map[selected_city]
        addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]

        if not addresses:
            styled_label(container, "No buildings found for this city.", fg="#C62828").pack(pady=10)
            btn_frame = tk.Frame(container, bg=BG)
            btn_frame.pack(pady=(12, 0))
            create_button(
                btn_frame,
                text="← Back",
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=self.step_city,
                next_window_func=None,
                current_window=None
            ).pack()
            return

        addr_cb = form_dropdown(container, "Address", addresses)

        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: self.step_details(selected_city, addr_cb.get()),
            next_window_func=None,
            current_window=None
        ).pack()

    # ---------------------------------------------------
    def step_details(self, city, address):
        clear_frame(self.box_frame)

        container = card(self.box_frame)

        styled_label(container, "Add Apartment", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 3 of 3 — Details", fg="#888").pack(pady=(0, 8))

        info = tk.Frame(container, bg="#F5F5F5", padx=12, pady=8)
        info.pack(fill="x", pady=(0, 12))
        styled_label(info, f"{city}  ·  {address}", fg="#555").pack(anchor="w")

        rooms_entry = form_field(container, "Number of Rooms", [0])
        type_cb     = form_dropdown(container, "Property Type", self.TYPES)
        occ_cb      = form_dropdown(container, "Occupancy Status", self.OCCUPANCY)

        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Add Apartment ✓",
            width=180,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: self._submit(
                rooms_entry.get(),
                type_cb.get(),
                occ_cb.get(),
                city, address
            ),
            next_window_func=None,
            current_window=None
        ).pack()

    # ---------------------------------------------------
    def _submit(self, rooms, apt_type, occ, city, address):
        building_id = self.display_to_id.get(address)
        city_id     = self.city_map[city]
        try:
            create_apartment(city_id, building_id, rooms, apt_type, occ)
            clear_frame(self.box_frame)
            styled_label(
                self.box_frame,
                "✓  Apartment added successfully!",
                fg="#2E7D32"
            ).pack(expand=True)
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", str(e))


# -------------------------------------------------------
def create_page(parent):
    return ApartmentManagerPage(parent).frame