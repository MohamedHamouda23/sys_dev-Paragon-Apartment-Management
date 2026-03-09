# log_in.py
import tkinter as tk
from tkinter import messagebox
from main.helpers import create_button, create_entry, create_navbar
from main.Dashbaord import page_template
from database.user_service import check_user, retrive_data

class Log_window:
    def __init__(self, main_window):
        self.main_window = main_window
        self.main_window.withdraw()  

        self.login_root = tk.Toplevel()
        self.login_root.title("Login")
        self.login_root.geometry("850x800")
        self.login_root.minsize(850, 800)
        self.login_root.configure(bg='#c9e4c4')

        self._create_navbar()
        self._create_login_frame()

    def _create_navbar(self):
        create_navbar(
            parent=self.login_root,
            logo_path="assets/Pams-logo.png",
            button_text="Back",
            button_command=self._go_back
        )

    def _create_login_frame(self):
        frame = tk.Frame(self.login_root, bg="#ffffff", width=400, height=350, relief="solid", border=1)
        frame.place(relx=0.5, rely=0.6, anchor="center")

        # Entries
        self.email_entry = create_entry(frame, 0, "Email", label_size=20)
        self.password_entry = create_entry(frame, 1, "Password", label_size=20, show="*")

        # Login button
        button_frame = tk.Frame(frame, bg="#ffffff")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        create_button(
            button_frame,
            text="Login",
            width=150,
            height=50,
            bg="red",
            fg="white",
            command=self.authenticate
        )

    def _go_back(self):
        self.login_root.destroy()
        self.main_window.deiconify()

    def authenticate(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        user = check_user(email, password)

        if user:
            user_info = retrive_data(email, password)
            self.login_root.destroy()
            page_template(self.main_window, user_info)
        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid credentials. Please check your email and password and try again.",
                parent=self.login_root,
            )

