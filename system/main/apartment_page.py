# ============================================================================
# APARTMENT PAGE
# Main page for viewing and managing apartments, cities, and buildings
# ============================================================================

import tkinter as tk
from tkinter import messagebox

from main.helpers import (
    create_button, clear_frame,
    styled_label, form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE, FONT_LABEL
)

from database.property_service import (
    get_all_cities,
    create_city,
    build_city_map,
    create_building,
    get_all_apartments
)

from modules.Property_Management import AddApartmentStepper
from validations import validate_city_name, validate_building_form


class ApartmentManagerPage:
    """Apartment management page with property/city/building actions"""

    def __init__(self, parent, user_info=None):
        # Store parent and user info
        self.parent = parent
        self.user_info = user_info
        
        # Create main frame
        self.frame = tk.Frame(parent, bg="#c9e4c4")

        # Top button bar
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")
        self.btns_inner_frame = btns_inner_frame
        
        # Create action buttons
        self.create_buttons()

        # Content area for table/forms
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))
        self.box_frame = content_frame
        
        # Load apartments
        self.refresh_apartments()

    # ========================================================================
    # CREATE BUTTONS
    # ========================================================================

    def create_buttons(self):
        """Create action buttons"""
        for text, command in [
            ("Add Property",  self.on_add_property),
            ("Add City",      self.show_add_city_stepper),
            ("Add Building",  self.show_add_building_stepper),
        ]:
            create_button(
                self.btns_inner_frame,
                text=text,
                width=140,
                height=45,
                bg="#3B86FF",
                fg="white",
                command=command,
                next_window_func=None,
                current_window=None
            ).pack(side="left", padx=8)

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
    # REFRESH APARTMENT LIST
    # ========================================================================

    def refresh_apartments(self):
        """Load and display all apartments in table"""
        clear_frame(self.box_frame)
        apartments = get_all_apartments()

        # Create table wrapper
        from tkinter import ttk
        table_wrap = tk.Frame(self.box_frame, bg="white", bd=2, relief="groove")
        table_wrap.pack(fill="both", expand=True, pady=(0, 12))

        # Show placeholder if no apartments
        if not apartments:
            styled_label(
                table_wrap,
                "Registered apartments will appear here",
                font=FONT_LABEL,
                fg="#888"
            ).pack(expand=True, pady=20)
            return

        # Create table columns
        columns = ("id", "city", "address", "postcode", "rooms", "type", "status")
        self.apt_tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=9)

        # Set column headings
        self.apt_tree.heading("id", text="ID")
        self.apt_tree.heading("city", text="City")
        self.apt_tree.heading("address", text="Address")
        self.apt_tree.heading("postcode", text="Postcode")
        self.apt_tree.heading("rooms", text="Rooms")
        self.apt_tree.heading("type", text="Type")
        self.apt_tree.heading("status", text="Status")

        # Set column widths
        self.apt_tree.column("id", width=55, anchor="center")
        self.apt_tree.column("city", width=120, anchor="w")
        self.apt_tree.column("address", width=180, anchor="w")
        self.apt_tree.column("postcode", width=110, anchor="w")
        self.apt_tree.column("rooms", width=70, anchor="center")
        self.apt_tree.column("type", width=110, anchor="w")
        self.apt_tree.column("status", width=110, anchor="w")

        # Add scrollbar
        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.apt_tree.yview)
        self.apt_tree.configure(yscrollcommand=y_scroll.set)

        # Pack table and scrollbar
        self.apt_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

        # Insert apartment rows
        for apt in apartments:
            self.apt_tree.insert("", "end", values=apt)

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def on_add_property(self):
        """Open add apartment wizard"""
        AddApartmentStepper(self.box_frame, self.refresh_apartments)

    # ========================================================================
    # ADD CITY
    # ========================================================================

    def show_add_city_stepper(self):
        """Show form to add new city"""
        clear_frame(self.box_frame)

        # Create form container
        container = card(self.box_frame)
        styled_label(container, "Add New City", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))

        # City name field (letters only)
        vcmd = container.register(lambda P: P.isalpha() or P == "")
        city_entry = form_field(container, "City Name", [0])
        city_entry.config(validate="key", validatecommand=(vcmd, "%P"))

        # Submit function
        def submit_city():
            city_name = city_entry.get()
            try:
                # Validate using centralized validation
                validate_city_name(city_name)
                
                # Create city in database
                create_city(city_name)
                self._show_success_state(
                    "City Added",
                    f"The city '{city_name}' was added successfully.",
                )
                self.box_frame.after(1200, self.refresh_apartments)
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e), parent=self.frame)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.frame)

        # Submit button
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

    # ========================================================================
    # ADD BUILDING
    # ========================================================================

    def show_add_building_stepper(self):
        """Show form to add new building"""
        clear_frame(self.box_frame)

        # Create form container
        container = card(self.box_frame)
        styled_label(container, "Add New Building", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))

        # Load cities
        cities     = get_all_cities()
        city_map   = build_city_map(cities)
        city_names = list(city_map.keys())

        # Create form fields
        city_cb        = form_dropdown(container, "Select City", city_names)
        street_entry   = form_field(container, "Street", [0])
        postcode_entry = form_field(container, "Postcode", [0])

        # Submit function
        def submit_building():
            selected_city = city_cb.get().strip()
            street = street_entry.get().strip()
            postcode = postcode_entry.get().strip()

            try:
                # Validate using centralized validation
                validate_building_form(selected_city, street, postcode)
                
                # Check city selection is valid
                if selected_city not in city_map:
                    raise ValueError("Please select a valid city.")
                
                # Create building in database
                city_id = city_map[selected_city]
                create_building(city_id, street, postcode)
                self._show_success_state(
                    "Building Added",
                    f"Building at {street} ({postcode}) was added for {selected_city}.",
                )
                self.box_frame.after(1200, self.refresh_apartments)
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e), parent=self.frame)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.frame)

        # Submit button
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


# ============================================================================
# LOGOUT FUNCTION
# ============================================================================

def logout_page(current_frame, parent_window):
    """Destroy current frame and show login window"""
    try:
        current_frame.destroy()
    except Exception:
        pass
    try:
        parent_window.deiconify()
    except Exception:
        pass
    from main.log_in import Log_window
    Log_window(parent_window)