# ============================================================================
# PROPERTY MANAGEMENT MODULE
# Handles apartment creation with city, building, and details steps
# ============================================================================

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

from validations import validate_apartment_form


# ============================================================================
# ADD APARTMENT STEPPER CLASS
# ============================================================================

class AddApartmentStepper:
    """Three-step wizard for adding apartments"""

    # Property type and occupancy options
    TYPES     = ['Studio', 'Apartment', 'Penthouse']
    OCCUPANCY = ['Occupied', 'Vacant', 'Unavailable']

    def __init__(self, parent, refresh_callback):
        # Store parent and refresh callback
        self.box_frame        = parent
        self.refresh_callback = refresh_callback

        # Load cities and buildings from database
        cities    = get_all_cities()
        buildings = get_all_buildings()

        # Build lookup dictionaries
        self.city_map          = build_city_map(cities)
        self.city_names        = list(self.city_map.keys())
        self.buildings_by_city, self.display_to_id = build_buildings_by_city(buildings)

        # Start with city selection
        self.step_city()

    # ========================================================================
    # SUCCESS STATE
    # ========================================================================

    def _show_success_state(self, title, detail):
        """Display success message and schedule refresh"""
        clear_frame(self.box_frame)

        # Create success card
        wrap = tk.Frame(self.box_frame, bg="#c9e4c4")
        wrap.pack(expand=True)

        card_frame = tk.Frame(wrap, bg="white", bd=2, relief="groove", padx=24, pady=18)
        card_frame.pack()

        # Success labels
        tk.Label(card_frame, text="SUCCESS", bg="white", fg="#2E7D32", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(card_frame, text=title, bg="white", fg="#1f3b63", font=("Arial", 16, "bold")).pack(anchor="w", pady=(4, 2))
        tk.Label(card_frame, text=detail, bg="white", fg="#4f5d73", font=("Arial", 11), justify="left").pack(anchor="w")
        tk.Label(card_frame, text="Returning to apartment list...", bg="white", fg="#777", font=("Arial", 10, "italic")).pack(anchor="w", pady=(10, 0))

    # ========================================================================
    # STEP 1: SELECT CITY
    # ========================================================================

    def step_city(self):
        """First step: Select city"""
        clear_frame(self.box_frame)

        # Create step container
        container = card(self.box_frame)
        styled_label(container, "Add Apartment", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 3 — Select City", fg="#888").pack(pady=(0, 8))

        # City dropdown
        city_cb = form_dropdown(container, "City", self.city_names)

        # Next button
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

    # ========================================================================
    # STEP 2: SELECT ADDRESS
    # ========================================================================

    def step_address(self, selected_city):
        """Second step: Select building address"""
        # Validate city selection
        if not selected_city:
            messagebox.showerror("Selection Error", "Please select a city before proceeding.", parent=self.box_frame)
            return
        if any(char.isdigit() for char in selected_city):
            messagebox.showerror("Input Error", "City names must only contain letters.", parent=self.box_frame)
            return

        clear_frame(self.box_frame)

        # Create step container
        container = card(self.box_frame)
        styled_label(container, "Add Apartment", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 3 — Select Address", fg="#888").pack(pady=(0, 8))
        styled_label(container, f"City: {selected_city}", fg="#555").pack(anchor="w")

        # Get addresses for selected city
        city_id   = self.city_map[selected_city]
        addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]

        # Check if addresses exist
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

        # Address dropdown
        addr_cb = form_dropdown(container, "Address", addresses)

        # Next button
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
        """Validate address selection and proceed"""
        if not selected_address:
            messagebox.showerror("Selection Error", "Please select an address before proceeding.", parent=self.box_frame)
            return
        self.step_details(selected_city, selected_address)

    # ========================================================================
    # STEP 3: APARTMENT DETAILS
    # ========================================================================

    def step_details(self, city, address):
        """Third step: Enter apartment details"""
        clear_frame(self.box_frame)

        # Create step container
        container = card(self.box_frame)
        styled_label(container, "Add Apartment", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 3 of 3 — Details", fg="#888").pack(pady=(0, 8))

        # Show selected city and address
        info = tk.Frame(container, bg="#F5F5F5", padx=12, pady=8)
        info.pack(fill="x", pady=(0, 12))
        styled_label(info, f"{city}  ·  {address}", fg="#555").pack(anchor="w")

        # Number of rooms (digits only)
        vcmd = container.register(lambda P: P.isdigit() or P == "")
        rooms_entry = form_field(container, "Number of Rooms", [0])
        rooms_entry.config(validate="key", validatecommand=(vcmd, "%P"))
        
        # Property type dropdown
        type_cb = form_dropdown(container, "Property Type", self.TYPES)
        
        # Occupancy status dropdown
        occ_cb = form_dropdown(container, "Occupancy Status", self.OCCUPANCY)

        # Auto-set rooms to 1 for Studio
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

        # Submit button
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

    # ========================================================================
    # SUBMIT
    # ========================================================================

    def _submit(self, rooms, apt_type, occ, city, address):
        """Validate and submit apartment data"""
        # Trim inputs
        rooms = (rooms or "").strip()
        apt_type = (apt_type or "").strip()
        occ = (occ or "").strip()

        # Validate using centralized validation
        try:
            validate_apartment_form(rooms, apt_type, occ)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self.box_frame)
            return

        # Get building and city IDs
        building_id = self.display_to_id.get(address)
        city_id     = self.city_map[city]
        
        if building_id is None:
            messagebox.showerror("Selection Error", "Please select a valid address.", parent=self.box_frame)
            return

        # Create apartment in database
        try:
            create_apartment(city_id, building_id, rooms, apt_type, occ)
            self._show_success_state(
                "Apartment Added",
                f"{apt_type} with {rooms} room(s) was added as {occ} in {city}.",
            )
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            error_text = str(e)
            if "CHECK constraint failed" in error_text and "occupancy_status" in error_text:
                messagebox.showerror("Input Error", "Please select a valid Occupancy Status.", parent=self.box_frame)
            else:
                messagebox.showerror("Error", error_text, parent=self.box_frame)


# ============================================================================
# PAGE FACTORY
# ============================================================================

def create_page(parent):
    """Create and return property management page"""
    from main.apartment_page import ApartmentManagerPage  
    return ApartmentManagerPage(parent).frame