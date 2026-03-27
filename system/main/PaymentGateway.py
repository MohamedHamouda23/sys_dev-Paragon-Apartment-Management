# PaymentGateway.py
import tkinter as tk
from tkinter import messagebox
from main.helpers import create_button
from database.tenant_portal_service import simulate_payment 

class PaymentWindow:
    def __init__(self, main_window, user_id, payment_id, outstanding, refresh_callback):
        self.main_window = main_window
        self.user_id = user_id
        self.payment_id = payment_id
        self.outstanding = outstanding
        self.refresh_callback = refresh_callback
        
        self.main_window.withdraw()
        self.root = tk.Toplevel()
        self.root.title("Secure Payment Gateway")
        self.root.geometry("400x500")
        self.root.configure(bg='white')

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="Payment Gateway", font=("Arial", 16, "bold"), bg="white").pack(pady=20)
        tk.Label(self.root, text=f"Balance Due: £{self.outstanding:.2f}", fg="red", bg="white", font=("Arial", 11, "bold")).pack()

        tk.Label(self.root, text="Amount to Pay (£):", bg="white").pack(pady=(20, 0))
        self.amt_entry = tk.Entry(self.root, font=("Arial", 12), justify="center")
        self.amt_entry.pack(pady=5)
        self.amt_entry.insert(0, f"{self.outstanding:.2f}")

        # Card Fields
        tk.Label(self.root, text="Cardholder Name", bg="white").pack(pady=(10,0))
        self.name_e = tk.Entry(self.root, width=30); self.name_e.pack()
        
        tk.Label(self.root, text="Card Number (16 Digits)", bg="white").pack(pady=(10,0))
        self.card_e = tk.Entry(self.root, width=30); self.card_e.pack()

        btn_f = tk.Frame(self.root, bg="white")
        btn_f.pack(pady=30)
        
        create_button(btn_f, text="Cancel", width=90, height=35, bg="#eee", command=self.close).pack(side="left", padx=10)
        create_button(btn_f, text="Pay Now", width=90, height=35, bg="#28a745", fg="white", command=self.process).pack(side="left", padx=10)

    def process(self):
        try:
            val = float(self.amt_entry.get())
            if val <= 0 or val > self.outstanding: raise ValueError
        except:
            messagebox.showerror("Error", "Enter a valid amount within the balance.")
            return

        if len(self.card_e.get().strip()) != 16:
            messagebox.showerror("Error", "Invalid card number.")
            return

        try:
            # Update DB with the NEW incremental amount
            simulate_payment(self.user_id, self.payment_id, val)
            messagebox.showinfo("Success", f"Payment of £{val:.2f} processed!")
            self.close()
            self.refresh_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def close(self):
        self.root.destroy()
        self.main_window.deiconify()