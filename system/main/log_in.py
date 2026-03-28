import tkinter as tk
from tkinter import messagebox

from main.helpers import (
    create_button,
    create_navbar,
    card,
    form_field,
    styled_label
)
from main.Dashbaord import page_template
from database.user_service import check_user, retrive_data


class Log_window:
    def __init__(self, main_window):
        self.main_window = main_window
        self.main_window.withdraw()

        self.login_root = tk.Toplevel()
        self.login_root.title("Login - Paragon Apartments")
        self.login_root.geometry("850x800")
        self.login_root.minsize(850, 800)
        self.login_root.configure(bg="#c9e4c4")

        self._show_password = False
        self._create_navbar()
        self._create_login_form()

    def _create_navbar(self):
        create_navbar(
            parent=self.login_root,
            logo_path="assets/Pams-logo.png",
            button_text="Back",
            button_command=self._go_back
        )

    def _create_login_form(self):
        # The wrapper ensures the card stays centered and matches the app background
        form_wrapper = tk.Frame(self.login_root, bg="#c9e4c4")
        form_wrapper.pack(fill="both", expand=True)

        # Spacer at the top to push the card down
        tk.Frame(form_wrapper, bg="#c9e4c4", height=70).pack()

        # --- CARD WIDENING & CLEANUP ---
        # We call the card and immediately configure it to remove grey borders
        self.card_inner = card(form_wrapper)
        
        # This removes the grey highlight/border often found in custom frame helpers
        self.card_inner.master.config(highlightthickness=0, bd=0, bg="#c9e4c4") 
        
        # Apply widening with ipadx and horizontal padding
        self.card_inner.pack_configure(ipadx=40, ipady=0, pady=0) 

        # Header
        tk.Label(
            self.card_inner,
            text="Welcome Back",
            font=("Arial", 26, "bold"), 
            bg="white",
            fg="#2c3e50"
        ).pack(pady=(30, 5))

        tk.Label(
            self.card_inner,
            text="Please enter your details to sign in",
            font=("Arial", 11),
            bg="white",
            fg="#7f8c8d"
        ).pack(pady=(0, 40))

        # Email
        self.email_entry = form_field(self.card_inner, "Email Address")

        # Password container
        pwd_container = tk.Frame(self.card_inner, bg="white")
        pwd_container.pack(fill="x", pady=(10, 5))

        self.password_entry = form_field(pwd_container, "Password")
        self.password_entry.config(show="*")

        # Toggle Button (Blue)
        toggle_frame = tk.Frame(self.card_inner, bg="white")
        toggle_frame.pack(anchor="e", pady=(5, 0), padx=10)

        self.toggle_btn = create_button(
            toggle_frame,
            text="Show Password",
            width=140,
            height=35,
            bg="#3B86FF",
            fg="white",
            command=self._toggle_password_visibility
        )

        # Login button container
        btn_frame = tk.Frame(self.card_inner, bg="white")
        btn_frame.pack(pady=(50, 40))

        create_button(
            btn_frame,
            text="Login",
            width=300, # Increased width for the "bit wide" card look
            height=55,
            bg="#f44336", # Standard clean red
            fg="white",
            command=self.authenticate
        )

    def _toggle_password_visibility(self):
        self._show_password = not self._show_password
        if self._show_password:
            self.password_entry.config(show="")
            self.toggle_btn.config(text="Hide Password")
        else:
            self.password_entry.config(show="*")
            self.toggle_btn.config(text="Show Password")

    def _go_back(self):
        self.login_root.destroy()
        self.main_window.deiconify()

    def authenticate(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        user = check_user(email, password)

        if user:
            user_info = retrive_data(email)
            self.login_root.destroy()
            page_template(self.main_window, user_info)
        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid credentials. Please check your email and password.",
                parent=self.login_root,
            )