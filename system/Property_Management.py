import tkinter as tk
from tkinter import ttk, messagebox
from helpers import create_button, create_entry
from database import get_cities,add_apartment


class AddApartmentPopup(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add Apartment")
        self.city_names, self.city_ids, self.buildings_by_city, self.display_to_id = get_cities()
        self.types = ['Studio', 'Apartment', 'Penthouse']
        self.occupancy = ['Occupied', 'Vacant', 'Unavailable']

        # City entry (for helper)
        self.city_var_entry = create_entry(
            self,
            2,
            "City",
            label_size=20,
            values=self.city_names
        )

        # Address dropdown
        self.address_var = create_entry(
            self,
            2,
            "Address",
            label_size=20,
            values=[]
        )
   
        # Number of rooms
        self.rooms_var = create_entry(
            self,
            row=3,
            label_text="Number of Rooms:",
            label_size=20,
            values=None
        )

        # Type dropdown
        self.type_var = create_entry(
            self,
            row=4,
            label_text="Type:",
            label_size=20,
            values=self.types
        )

        # Occupancy dropdown
        self.occ_var = create_entry(
            self,
            row=5,
            label_text="Occupancy:",
            label_size=20,
            values=self.occupancy
        )

        # Submit button
        tk.Button(self, text="Add Apartment", command=self.submit).pack(pady=10)

    def update_addresses(self, *args):
        selected_city = self.city_var.get()
        if selected_city:
            city_id = self.city_ids[selected_city]
            addresses = [display for _, display in self.buildings_by_city.get(city_id, [])]
            self.address_dropdown['values'] = addresses
            self.address_var.set('' if not addresses else addresses[0])
        else:
            self.address_dropdown['values'] = []
            self.address_var.set('')

    def submit(self):
        city, address, num_rooms, apt_type, occ = (
        self.city_var.get(),
        self.address_var.get(),
        self.rooms_var.get(),
        self.type_var.get(),
        self.occ_var.get()
    )
        if not (city and address and num_rooms and apt_type and occ):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            city_id = self.city_ids[city]
            building_id = self.display_to_id.get(address)
            if building_id is None:
                messagebox.showerror("Error", "Invalid building selection.")
                return
            add_apartment(city_id, building_id, num_rooms, apt_type, occ)
            messagebox.showinfo("Success", "Apartment added!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class ApartmentsPage:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent, bg='#c9e4c4')
        self.build_ui()

    def build_ui(self):
        # Top buttons frame
        top_btn_frame = tk.Frame(self.frame, bg='#c9e4c4')
        top_btn_frame.pack(side="top", fill="x", pady=(30, 10))

        btns_inner_frame = tk.Frame(top_btn_frame, bg='#c9e4c4')
        btns_inner_frame.pack(anchor="center")

        # Add Property button
        btn_add_property = create_button(
            btns_inner_frame,
            text="Add Property",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: AddApartmentPopup(self.frame)
        )
        btn_add_property.pack(side="left", padx=(0, 120))

        # Add City button
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

        # Apartments display box
        box_frame = tk.Frame(self.frame, bg="white", bd=2, relief="groove")
        box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

        placeholder_label = tk.Label(
            box_frame,
            text="Registered apartments will appear here",
            font=("Arial", 16),
            bg="white",
            fg="#888"
        )
        placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    def get_frame(self):
        return self.frame
