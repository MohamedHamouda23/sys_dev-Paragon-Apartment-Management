import tkinter as tk
from tkinter import messagebox


from main.helpers import (
    create_button, clear_frame,
    styled_label, form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE
)

from database.property_service import (
    get_all_cities,
    get_all_buildings,
    build_city_map,
    build_buildings_by_city,
    create_apartment
)


# =======================================================
# APARTMENT STEPPER
# =======================================================
class AddApartmentStepper:

    TYPES     = ['Studio', 'Apartment', 'Penthouse']
    OCCUPANCY = ['Occupied', 'Vacant', 'Unavailable']

    def __init__(self, parent, refresh_callback):
        self.box_frame        = parent
        self.refresh_callback = refresh_callback

        cities    = get_all_cities()
        buildings = get_all_buildings()

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
        if not selected_city:
            messagebox.showerror("Selection Error", "Please select a city before proceeding.")
            return
        if any(char.isdigit() for char in selected_city):
            messagebox.showerror("Input Error", "City names must only contain letters.")
            return

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
            command=lambda: self._address_next(selected_city, addr_cb.get()),
            next_window_func=None,
            current_window=None
        ).pack()

    def _address_next(self, selected_city, selected_address):
        if not selected_address:
            messagebox.showerror("Selection Error", "Please select an address before proceeding.")
            return
        self.step_details(selected_city, selected_address)

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

        # Only allow numbers in Number of Rooms
        vcmd = container.register(lambda P: P.isdigit() or P == "")
        rooms_entry = form_field(container, "Number of Rooms", [0])
        rooms_entry.config(validate="key", validatecommand=(vcmd, "%P"))
        type_cb     = form_dropdown(container, "Property Type", self.TYPES)
        occ_cb      = form_dropdown(container, "Occupancy Status", self.OCCUPANCY)

        # --- Room entry logic based on property type ---
        def on_type_change(event=None):
            selected_type = type_cb.get()
            if selected_type == "Studio":
                rooms_entry.config(state="normal")
                rooms_entry.delete(0, tk.END)
                rooms_entry.insert(0, "1")
                rooms_entry.config(state="disabled", disabledbackground="#eee", disabledforeground="#888")
            else:
                rooms_entry.config(state="normal")
                rooms_entry.delete(0, tk.END)

        type_cb.bind("<<ComboboxSelected>>", on_type_change)
        on_type_change()

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
            styled_label(self.box_frame, "✓  Apartment added successfully!", fg="#2E7D32").pack(expand=True)
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", str(e))


def create_page(parent):
    from main.apartment_page import ApartmentManagerPage  
    return ApartmentManagerPage(parent).frame