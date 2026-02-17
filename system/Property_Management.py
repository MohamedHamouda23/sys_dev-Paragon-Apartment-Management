import tkinter as tk
from tkinter import ttk, messagebox
from helpers import create_button
from database import check_connection

# Helper for styled button
def styled_button(parent, **kwargs):
    return tk.Button(parent, font=("Arial", 12, "bold"), bg="#3B86FF", fg="white", relief="raised", bd=2, padx=10, pady=4, activebackground="#1c5db6", activeforeground="white", cursor="hand2", **kwargs)

def create_page(parent):
    frame = tk.Frame(parent, bg='#c9e4c4')

    # Top buttons frame (centered)
    top_btn_frame = tk.Frame(frame, bg='#c9e4c4')
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10))

    # Centering inner frame for buttons
    btns_inner_frame = tk.Frame(top_btn_frame, bg='#c9e4c4')
    btns_inner_frame.pack(anchor="center")


    # Add all three buttons in a single, correct place
    def refresh_apartments():
        for widget in box_frame.winfo_children():
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
                box_frame,
                text="Registered apartments will appear here",
                font=("Arial", 16),
                bg="white",
                fg="#888")
            placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            for apt in apartments:
                apt_str = f"{apt[1]} | {apt[2]} ({apt[3]}) | Rooms: {apt[4]} | Type: {apt[5]} | Status: {apt[6]}"
                tk.Label(box_frame, text=apt_str, anchor="w", bg="white", font=("Arial", 12)).pack(fill="x", padx=10, pady=2)

    def on_add_property():
        show_add_apartment_stepper(frame, box_frame, refresh_apartments)


    # Create all three buttons, blue color, no duplicates
    add_property_btn = create_button(
        btns_inner_frame,
        text="Add Property",
        bg="#3B86FF",
        fg="white",
        command=on_add_property
    )
    add_property_btn.pack(side="left", padx=(0, 15), pady=10)

    add_city_btn = create_button(
        btns_inner_frame,
        text="Add City",
        bg="#3B86FF",
        fg="white",
        command=lambda: show_add_city_stepper(frame, box_frame, refresh_apartments)
    )
    add_city_btn.pack(side="left", padx=(0, 15), pady=10)

    add_building_btn = create_button(
        btns_inner_frame,
        text="Add Building",
        bg="#3B86FF",
        fg="white",
        command=lambda: show_add_building_stepper(frame, box_frame, refresh_apartments)
    )
    add_building_btn.pack(side="left", padx=(0, 0), pady=10)

    # Big box for apartments
    box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    def show_add_city_stepper(parent, box_frame, refresh_apartments_callback):
        for widget in box_frame.winfo_children():
            widget.destroy()
        tk.Label(box_frame, text="Add New City:").pack(pady=(20, 5))
        city_var = tk.StringVar()
        city_entry = tk.Entry(box_frame, textvariable=city_var, width=30)
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
                for widget in box_frame.winfo_children():
                    widget.destroy()
                tk.Label(box_frame, text="City added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
                box_frame.after(1200, refresh_apartments_callback)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(box_frame, text="Add City", command=submit_city).pack(pady=10)

    # Removed duplicate Add City button

    def show_add_building_stepper(parent, box_frame, refresh_apartments_callback):
        for widget in box_frame.winfo_children():
            widget.destroy()
        tk.Label(box_frame, text="Add New Building:").pack(pady=(20, 5))
        # Fetch cities for dropdown
        conn = check_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT city_id, city_name FROM Location")
        cities = cursor.fetchall()
        conn.close()
        city_names = [c[1] for c in cities]
        city_ids = {c[1]: c[0] for c in cities}
        tk.Label(box_frame, text="Select City:").pack()
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(box_frame, textvariable=city_var, values=city_names, state="readonly")
        city_dropdown.pack()
        tk.Label(box_frame, text="Street Address:").pack()
        street_var = tk.StringVar()
        street_entry = tk.Entry(box_frame, textvariable=street_var, width=40)
        street_entry.pack()
        tk.Label(box_frame, text="Postcode:").pack()
        postcode_var = tk.StringVar()
        postcode_entry = tk.Entry(box_frame, textvariable=postcode_var, width=20)
        postcode_entry.pack()
        def submit_building():
            city = city_dropdown.get()
            street = street_entry.get().strip()
            postcode = postcode_entry.get().strip()
            if not (city and street and postcode):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                city_id = city_ids[city]
                conn = check_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Buildings (city_id, street, postcode) VALUES (?, ?, ?)", (city_id, street, postcode))
                conn.commit()
                conn.close()
                for widget in box_frame.winfo_children():
                    widget.destroy()
                tk.Label(box_frame, text="Building added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
                box_frame.after(1200, refresh_apartments_callback)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(box_frame, text="Add Building", command=submit_building).pack(pady=10)



    # For all labels in box_frame, set wraplength and justify
    def wrap_labels():
        for widget in box_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(wraplength=box_frame.winfo_width()-40, justify="left")
    box_frame.bind("<Configure>", lambda e: wrap_labels())

    refresh_apartments()
    return frame

def show_add_apartment_stepper(parent, box_frame, refresh_apartments_callback):
    # Fetch cities from DB
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city_id, city_name FROM Location")
    cities = cursor.fetchall()
    city_names = [c[1] for c in cities]
    city_ids = {c[1]: c[0] for c in cities}

    # Fetch all buildings and organize by city_id, include postcode
    cursor.execute("SELECT building_id, city_id, street, postcode FROM Buildings")
    buildings = cursor.fetchall()
    buildings_by_city = {}
    display_to_id = {}
    for b_id, c_id, street, postcode in buildings:
        display = f"{street} ({postcode})"
        buildings_by_city.setdefault(c_id, []).append((b_id, display))
        display_to_id[display] = b_id
    conn.close()

    types = ['Studio', 'Apartment', 'Penthouse']
    occupancy = ['Occupied', 'Vacant', 'Unavailable']

    # Step 1: Select City
    def step_city():
        for widget in box_frame.winfo_children():
            widget.destroy()
        tk.Label(box_frame, text="Select City:").pack()
        city_var = tk.StringVar()
        city_dropdown = ttk.Combobox(box_frame, textvariable=city_var, values=city_names, state="readonly")
        city_dropdown.pack()
        def next_to_address():
            city = city_dropdown.get()  # FIX: Use combobox get() instead of StringVar
            if not city:
                messagebox.showerror("Error", "Please select a city.")
                return
            step_address(city)
        tk.Button(box_frame, text="Next", command=next_to_address).pack(pady=10)

    # Step 2: Select Address
    def step_address(selected_city):
        for widget in box_frame.winfo_children():
            widget.destroy()
        tk.Label(box_frame, text=f"City: {selected_city}").pack()
        tk.Label(box_frame, text="Select Address:").pack()
        address_var = tk.StringVar()
        city_id = city_ids[selected_city]
        addresses = [display for _, display in buildings_by_city.get(city_id, [])]
        if not addresses:
            tk.Label(box_frame, text="No buildings available in this city.", fg="red", font=("Arial", 12)).pack(pady=10)
            tk.Button(box_frame, text="Back", command=step_city).pack(pady=10)
            return
        address_dropdown = ttk.Combobox(box_frame, textvariable=address_var, values=addresses, state="readonly", width=40)  # Wider dropdown
        address_dropdown.pack()
        def next_to_details():
            address = address_dropdown.get()  # FIX: Use combobox get() instead of StringVar
            if not address:
                messagebox.showerror("Error", "Please select an address.")
                return
            step_details(selected_city, address)
        tk.Button(box_frame, text="Next", command=next_to_details).pack(pady=10)

    # Step 3: Apartment Details
    def step_details(selected_city, selected_address):
        for widget in box_frame.winfo_children():
            widget.destroy()
        tk.Label(box_frame, text=f"City: {selected_city}").pack()
        tk.Label(box_frame, text=f"Address: {selected_address}").pack()
        tk.Label(box_frame, text="Number of Rooms:").pack()
        rooms_entry = tk.Entry(box_frame)
        rooms_entry.pack()
        tk.Label(box_frame, text="Type:").pack()
        type_var = tk.StringVar()
        type_dropdown = ttk.Combobox(box_frame, textvariable=type_var, values=types, state="readonly")
        type_dropdown.pack()
        tk.Label(box_frame, text="Occupancy:").pack()
        occ_var = tk.StringVar()
        occ_dropdown = ttk.Combobox(box_frame, textvariable=occ_var, values=occupancy, state="readonly")
        occ_dropdown.pack()
        def submit():
            num_rooms = rooms_entry.get()
            apt_type = type_dropdown.get()  # FIX: get value from combobox directly
            occ = occ_dropdown.get()        # FIX: get value from combobox directly
            print(f"num_rooms: {num_rooms}, apt_type: {apt_type}, occ: {occ}")
            if not (num_rooms and apt_type and occ):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                city_id = city_ids[selected_city]
                building_id = display_to_id.get(selected_address)
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
                for widget in box_frame.winfo_children():
                    widget.destroy()
                tk.Label(box_frame, text="Apartment added successfully!", fg="green", font=("Arial", 14)).pack(pady=20)
                box_frame.after(1200, refresh_apartments_callback)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(box_frame, text="Add Apartment", command=submit).pack(pady=10)

    step_city()