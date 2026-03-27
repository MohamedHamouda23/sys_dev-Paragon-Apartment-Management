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
        self.outstanding = float(outstanding or 0)
        self.refresh_callback = refresh_callback
        self.mode = tk.StringVar(value="partial")  # Default to custom amount
        
        # Add a flag to prevent recursive calls
        self.updating = False

        self.root = tk.Toplevel(self.main_window)
        self.root.title("Secure Payment Gateway")
        self.root.geometry("400x560")
        self.root.configure(bg="white")
        self.root.transient(self.main_window)
        self.root.grab_set()

        self.setup_ui()

    def setup_ui(self):
        tk.Label(
            self.root,
            text="Payment Gateway",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=20)

        tk.Label(
            self.root,
            text=f"Balance Due: £{self.outstanding:.2f}",
            fg="red",
            bg="white",
            font=("Arial", 11, "bold")
        ).pack()

        tk.Label(self.root, text="Payment Type", bg="white").pack(pady=(20, 0))

        tk.Radiobutton(
            self.root,
            text="Full Amount",
            variable=self.mode,
            value="full",
            bg="white",
            command=self.on_full_selected
        ).pack()

        tk.Radiobutton(
            self.root,
            text="Custom Amount",
            variable=self.mode,
            value="partial",
            bg="white",
            command=self.on_custom_selected
        ).pack()

        tk.Label(self.root, text="Amount to Pay (£):", bg="white").pack(pady=(20, 0))
        self.amt_entry = tk.Entry(self.root, font=("Arial", 12), justify="center", state="normal")
        self.amt_entry.pack(pady=5)
        
        # Bind events to ensure entry is editable
        self.amt_entry.bind("<FocusIn>", self.on_entry_focus)

        tk.Label(self.root, text="Cardholder Name", bg="white").pack(pady=(10, 0))
        self.name_e = tk.Entry(self.root, width=30)
        self.name_e.pack()

        tk.Label(self.root, text="Card Number (16 Digits)", bg="white").pack(pady=(10, 0))
        self.card_e = tk.Entry(self.root, width=30)
        self.card_e.pack()

        btn_f = tk.Frame(self.root, bg="white")
        btn_f.pack(pady=30)

        create_button(
            btn_f,
            text="Cancel",
            width=90,
            height=35,
            bg="#eee",
            command=self.close
        ).pack(side="left", padx=10)

        create_button(
            btn_f,
            text="Pay Now",
            width=90,
            height=35,
            bg="#28a745",
            fg="white",
            command=self.process
        ).pack(side="left", padx=10)

        # Initialize with custom amount (empty field ready for input)
        self.set_custom_amount()
        
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def on_full_selected(self):
        """Handle full amount selection"""
        if self.updating:
            return
        self.updating = True
        self.set_full_amount()
        self.updating = False
    
    def on_custom_selected(self):
        """Handle custom amount selection"""
        if self.updating:
            return
        self.updating = True
        self.set_custom_amount()
        self.updating = False
    
    def set_full_amount(self):
        """Set the entry for full amount (disabled)"""
        # First make sure entry is normal so we can modify it
        self.amt_entry.config(state="normal")
        self.amt_entry.delete(0, tk.END)
        self.amt_entry.insert(0, f"{self.outstanding:.2f}")
        # Then disable it
        self.amt_entry.config(state="disabled", disabledbackground="#f0f0f0")
    
    def set_custom_amount(self):
        """Set the entry for custom amount (enabled and editable)"""
        # Make sure entry is normal
        self.amt_entry.config(state="normal")
        # Clear the entry
        self.amt_entry.delete(0, tk.END)
        # Set focus so user can type immediately
        self.amt_entry.focus_set()
        # Force the entry to be editable
        self.amt_entry.config(state="normal", background="white")
    
    def on_entry_focus(self, event):
        """Handle focus events on the amount entry"""
        # If we're in custom mode and entry is disabled, enable it
        if self.mode.get() == "partial":
            if self.amt_entry.cget('state') == 'disabled':
                self.amt_entry.config(state="normal")
                self.amt_entry.delete(0, tk.END)

    def _toggle_amount_entry(self):
        """Legacy method - kept for compatibility but not used"""
        pass

    def process(self):
        """Process the payment"""
        current_mode = self.mode.get()
        
        try:
            # Get the payment amount based on selected mode
            if current_mode == "full":
                val = self.outstanding
            else:
                # For custom amount, ensure entry is enabled
                if self.amt_entry.cget('state') == 'disabled':
                    self.amt_entry.config(state="normal")
                
                # Get and validate custom amount
                amount_text = self.amt_entry.get().strip()
                print(f"Custom amount entered: '{amount_text}'")  # Debug print
                
                if not amount_text:
                    raise ValueError("Please enter an amount")
                
                # Check if it's a valid number
                try:
                    val = float(amount_text)
                except ValueError:
                    raise ValueError("Please enter a valid number (e.g., 50.00)")
                
                if val <= 0:
                    raise ValueError("Amount must be greater than 0")
                if val > self.outstanding + 0.01:  # Allow small rounding differences
                    raise ValueError(f"Amount cannot exceed balance of £{self.outstanding:.2f}")
                
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Validate cardholder name
        cardholder = self.name_e.get().strip()
        if not cardholder:
            messagebox.showerror("Error", "Please enter the cardholder name.")
            return

        # Validate card number
        card_number = self.card_e.get().strip()
        if not card_number:
            messagebox.showerror("Error", "Please enter the card number.")
            return
        if not card_number.isdigit():
            messagebox.showerror("Error", "Card number must contain only digits.")
            return
        if len(card_number) != 16:
            messagebox.showerror("Error", "Card number must be exactly 16 digits.")
            return

        # Process the payment
        try:
            simulate_payment(self.user_id, self.payment_id, val, current_mode)
            messagebox.showinfo("Success", f"Payment of £{val:.2f} processed successfully!")
            self.close()
            if self.refresh_callback:
                self.refresh_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Payment failed: {str(e)}")

    def close(self):
        """Close the payment window"""
        try:
            self.root.grab_release()
        except Exception:
            pass
        self.root.destroy()