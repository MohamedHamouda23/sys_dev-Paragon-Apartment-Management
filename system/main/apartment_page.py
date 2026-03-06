import tkinter as tk
from tkinter import messagebox

from main.helpers import (
    create_button, create_frame, clear_frame,
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

        from main.helpers import create_logout_button
        create_logout_button(self.btns_inner_frame, self.frame, self.parent)

    # ---------------------------------------------------
    def refresh_apartments(self):
        clear_frame(self.box_frame)
        apartments = get_all_apartments()

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

        # Only allow letters in City Name
        vcmd = container.register(lambda P: P.isalpha() or P == "")
        city_entry = form_field(container, "City Name", [0])
        city_entry.config(validate="key", validatecommand=(vcmd, "%P"))

        def submit_city():
            city_name = city_entry.get()
            if not city_name.isalpha():
                messagebox.showerror("Input Error", "City names must only contain letters.")
                return
            try:
                create_city(city_name)
                clear_frame(self.box_frame)
                styled_label(self.box_frame, "✓  City added successfully!", fg="#2E7D32").pack(expand=True)
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

        cities     = get_all_cities()
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
                styled_label(self.box_frame, "✓  Building added successfully!", fg="#2E7D32").pack(expand=True)
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



def logout_page(current_frame, parent_window):
    """
    Destroys the current frame, shows the parent window, and opens the login window.
    """
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