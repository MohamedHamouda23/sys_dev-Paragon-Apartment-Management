# Log_in.py
import tkinter as tk
from tkinter import messagebox
from main.helpers import create_button, create_entry, create_navbar
from main.Dashbaord import page_template 

class PaymentWindow:
    def __init__(self, main_window):
        self.main_window = main_window
        self.main_window.withdraw()  # Hide main window
        
        self.root = tk.Toplevel()
        self.root.title("Secure Payment")
        self.root.geometry("850x800")
        self.root.minsize(850, 800)
        self.root.configure(bg='#c9e4c4')

        self.setup_ui()

    def setup_ui(self):
        """Setup all UI elements."""
        # --- CARD FORM FRAME ---
        self.frame = tk.Frame(self.root, bg="#ffffff", width=400, height=500,
                              relief="solid", borderwidth=1)
        self.frame.place(relx=0.5, rely=0.55, anchor="center")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        # Amount Entry
        self.amount_entry = tk.Entry(self.frame, font=("Arial", 14), justify="center")
        self.amount_entry.grid(row=1, column=0, columnspan=2, pady=(20, 15), ipadx=40, ipady=6)

        # Cardholder
        tk.Label(self.frame, text="Cardholder Name", font=("Arial", 14), bg="#ffffff")\
            .grid(row=2, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")
        self.cardholder_entry = tk.Entry(self.frame, font=("Arial", 14))
        self.cardholder_entry.grid(row=3, column=0, columnspan=2, padx=10, pady=(0,10), sticky="ew", ipadx=10, ipady=5)

        # Card Number
        tk.Label(self.frame, text="Card Number", font=("Arial", 14), bg="#ffffff")\
            .grid(row=4, column=0, columnspan=2, padx=10, pady=(10,0), sticky="w")
        self.card_number_entry = tk.Entry(self.frame, font=("Arial", 14))
        self.card_number_entry.grid(row=5, column=0, columnspan=2, padx=10, pady=(0,10), sticky="ew", ipadx=10, ipady=5)

        # CVC + Expiry
        tk.Label(self.frame, text="CVC", font=("Arial", 14), bg="#ffffff")\
            .grid(row=6, column=0, padx=10, pady=(10,0), sticky="w")
        self.cvc_entry = tk.Entry(self.frame, font=("Arial", 14))
        self.cvc_entry.grid(row=7, column=0, padx=10, pady=(0,10), sticky="ew", ipadx=10, ipady=5)

        tk.Label(self.frame, text="Expiry Date (MM/YY)", font=("Arial", 14), bg="#ffffff")\
            .grid(row=6, column=1, padx=10, pady=(10,0), sticky="w")
        self.expiry_entry = tk.Entry(self.frame, font=("Arial", 14))
        self.expiry_entry.grid(row=7, column=1, padx=10, pady=(0,10), sticky="ew", ipadx=10, ipady=5)

        # Buttons
        button_frame1 = tk.Frame(self.frame, bg="#ffffff")
        button_frame1.grid(row=8, column=0, pady=20)
        button_frame2 = tk.Frame(self.frame, bg="#ffffff")
        button_frame2.grid(row=8, column=1, pady=20)

        create_button(
            button_frame1,
            text="Cancel",
            width=150,
            height=50,
            bg="white",
            fg="red",
            command=self.cancel_payment
        )

        create_button(
            button_frame2,
            text="Pay Now",
            width=150,
            height=50,
            bg="red",
            fg="white",
            command=self.validate_payment
        )

    def validate_payment(self):
        """Validate payment card information."""
        card_number = self.card_number_entry.get().strip()
        cvc = self.cvc_entry.get().strip()
        cardholder = self.cardholder_entry.get().strip()
        
        if not cardholder or not card_number or not cvc:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if len(card_number) != 16 or not card_number.isdigit():
            messagebox.showerror("Error", "Card number must be 16 digits")
            return
        
        if len(cvc) != 3 or not cvc.isdigit():
            messagebox.showerror("Error", "CVC must be 3 digits")
            return
        
        messagebox.showinfo("Success", "Payment processed successfully")
        self.root.destroy()
        self.main_window.deiconify()

    def cancel_payment(self):
        """Cancel payment and return to main window."""
        self.root.destroy()
        self.main_window.deiconify()


