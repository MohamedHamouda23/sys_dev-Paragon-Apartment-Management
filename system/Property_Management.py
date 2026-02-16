

import tkinter as tk
from tkinter import ttk, messagebox
from helpers import create_button
from database import check_connection




def show_add_apartment_popup(parent):
    popup = tk.Toplevel(parent)
    popup.title("Add Apartment")
    popup.geometry("400x400")

    # Fetch cities from DB
    conn = check_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city_id, city_name FROM Location")
    cities = cursor.fetchall()
    conn.close()

    city_names = [c[1] for c in cities]
    city_ids = {c[1]: c[0] for c in cities}

    types = ['Studio', 'One Bedroom', 'Two Bedroom', 'Three Bedroom', 'Penthouse']
    occupancy = ['Occupied', 'Vacant', 'Unavailable']

    tk.Label(popup, text="City:").pack()
    city_var = tk.StringVar()
    city_dropdown = ttk.Combobox(popup, textvariable=city_var, values=city_names, state="readonly")
    city_dropdown.pack()

    tk.Label(popup, text="Address:").pack()
    address_entry = tk.Entry(popup)
    address_entry.pack()

    tk.Label(popup, text="Number of Rooms:").pack()
    rooms_entry = tk.Entry(popup)
    rooms_entry.pack()

    tk.Label(popup, text="Type:").pack()
    type_var = tk.StringVar()
    type_dropdown = ttk.Combobox(popup, textvariable=type_var, values=types, state="readonly")
    type_dropdown.pack()

    tk.Label(popup, text="Occupancy:").pack()
    occ_var = tk.StringVar()
    occ_dropdown = ttk.Combobox(popup, textvariable=occ_var, values=occupancy, state="readonly")
    occ_dropdown.pack()

    def submit():
        city = city_var.get()
        address = address_entry.get()
        num_rooms = rooms_entry.get()
        apt_type = type_var.get()
        occ = occ_var.get()
        if not (city and address and num_rooms and apt_type and occ):
            messagebox.showerror("Error", "All fields are required.")
            return
        try:
            conn = check_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Apartments (city_id, address, num_rooms, type, occupancy_status) VALUES (?, ?, ?, ?, ?)",
                (city_ids[city], address, int(num_rooms), apt_type, occ)
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Apartment added!")
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(popup, text="Add Apartment", command=submit).pack(pady=10)

def create_page(parent):
    frame = tk.Frame(parent, bg='#c9e4c4')

    # Top buttons frame (centered)
    top_btn_frame = tk.Frame(frame, bg='#c9e4c4')
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10))

    # Centering inner frame for buttons
    btns_inner_frame = tk.Frame(top_btn_frame, bg='#c9e4c4')
    btns_inner_frame.pack(anchor="center")

    btn_add_property = create_button(
        btns_inner_frame,
        text="Add Property",
        width=150,
        height=50,
        bg="#3B86FF",
        fg="white",
        command=lambda: show_add_apartment_popup(frame)
    )
    btn_add_property.pack(side="left", padx=(0, 120))

    btn_add_city = create_button(
        btns_inner_frame,
        text="Add City",
        width=150,
        height=50,
        bg="#3B86FF",
        fg="white",
        command=None
    )
    btn_add_city.pack(side="left")

    # Big box for apartments
    box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    placeholder_label = tk.Label(
        box_frame,
        text="Registered apartments will appear here",
        font=("Arial", 16),
        bg="white",
        fg="#888"
    )
    placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    return frame
