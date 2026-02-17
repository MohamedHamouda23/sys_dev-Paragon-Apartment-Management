import tkinter as tk
from tkinter import ttk, messagebox
from helpers import create_button, create_frame
from database import check_connection

class ApartmentManagerPage:
    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        self.city_ids = {}
        self.buildings_by_city = {}
        self.display_to_id = {}

        self.create_buttons()
        self.wrap_labels()
        self.refresh_apartments()

    # ---------------------- Buttons ----------------------
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

    # ---------------------- Apartment Display ----------------------
    def refresh_apartments(self):
        for widget in self.box_frame.winfo_children():
            widget.destroy()

        conn = check_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.apartment_id, l.city_name, b.street, b.postcode, a.num_rooms, a.type, a.occupancy_status
            FROM Apartments a
            JOIN Location l ON a.city_id = l.city_id
            JOIN Buildings b ON a.building_id = b.building_id
        """)
        apartments = cursor.fetchall()
        conn.close()

        if not apartments:
            placeholder_label = tk.Label(
                self.box_frame,
                text="Registered apartments will appear here",
                font=("Arial", 16),
                bg="white",
                fg="#888"
            )
            placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
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
                conn = check_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Location (city_name) VALUES (?)", (city_name,))
                conn.commit()
                conn.close()
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

        # Fetch cities for dropdown
        conn = check_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT city_id, city_name FROM Location")
        cities = cursor.fetchall()
        conn.close()
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
                conn = check_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Buildings (city_id, street, postcode) VALUES (?, ?, ?)",
                               (city_id, street, postcode))
                conn.commit()
                conn.close()
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
        self.load_data()
        self.step_city()

    def load_data(self):
        conn = check_connection()
        cursor = conn.cursor()
        # Cities
        cursor.execute("SELECT city_id, city_name FROM Location")
        cities = cursor.fetchall()
        self.city_ids = {c[1]: c[0] for c in cities}
        self.city_names = [c[1] for c in cities]
        # Buildings
        cursor.execute("SELECT building_id, city_id, street, postcode FROM Buildings")
        buildings = cursor.fetchall()
        for b_id, c_id, street, postcode in buildings:
            display = f"{street} ({postcode})"
            self.buildings_by_city.setdefault(c_id, []).append((b_id, display))
            self.display_to_id[display] = b_id
        conn.close()
        self.types = ['Studio', 'Apartment', 'Penthouse']
        self.occupancy = ['Occupied', 'Vacant', 'Unavailable']

    # ---------------------- Steps ----------------------
    def step_city(self):
        for widget in self.box_frame.winfo_children():
            widget.destroy()
        tk.Label(self.box_frame, text="Select City:").pack()
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(self.box_frame, textvariable=city_var, values=self.city_names, state="readonly")
        city_dropdown.pack()
        tk.Button(self.box_frame, text="Next", command=lambda: self.step_address(city_dropdown.get())).pack(pady=10)

    def step_address(self, selected_city):
        for widget in self.box_frame.winfo_children():
            widget.destroy()
        tk.Label(self.box_frame, text=f"City: {selected_city}").pack()
        tk.Label(self.box_frame, text="Select Address:").pack()
        address_var = tk.StringVar()
        city_id = self.city_ids[selected_city]
        addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]
        if not addresses:
            tk.Label(self.box_frame, text="No buildings available in this city.", fg="red", font=("Arial", 12)).pack(pady=10)
            tk.Button(self.box_frame, text="Back", command=self.step_city).pack(pady=10)
            return
        address_dropdown = ttk.Combobox(self.box_frame, textvariable=address_var, values=addresses, state="readonly", width=40)
        address_dropdown.pack()
        tk.Button(self.box_frame, text="Next", command=lambda: self.step_details(selected_city, address_dropdown.get())).pack(pady=10)

    def step_details(self, selected_city, selected_address):
        for widget in self.box_frame.winfo_children():
            widget.destroy()
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

        tk.Button(self.box_frame, text="Add Apartment", command=lambda: self.submit(
            rooms_entry.get(), type_dropdown.get(), occ_dropdown.get(), selected_city, selected_address
        )).pack(pady=10)

    def submit(self, num_rooms, apt_type, occ, selected_city, selected_address):
        if not (num_rooms and apt_type and occ):
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            city_id = self.city_ids[selected_city]
            building_id = self.display_to_id.get(selected_address)
            if building_id is None:
                messagebox.showerror("Error", "Invalid building selection.")
                return
            conn = check_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Apartments (city_id, building_id, num_rooms, type, occupancy_status) VALUES (?, ?, ?, ?, ?)",
                (city_id, building_id, int(num_rooms), apt_type, occ)
            )
            conn.commit()
            conn.close()
            for widget in self.box_frame.winfo_children():
                widget.destroy()
            tk.Label(self.box_frame, text="Apartment added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
            self.box_frame.after(1200, self.refresh_callback)
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ---------------------- Usage ----------------------
def create_page(parent):
    page = ApartmentManagerPage(parent)
    return page.frame
