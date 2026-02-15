# Log_in.py
import tkinter as tk
from helpers import create_button, create_entry, create_navbar
from Dashbaord import page_template
from PaymentGateway import payment_window 
from database import check_user,retrive_data

def Log_in(email_entry, password_entry):
    return email_entry.get(), password_entry.get()


def authentication(email_entry, password_entry,login_window, main_window):
    email, password = Log_in(email_entry, password_entry)

    user = check_user(email, password)

    if user:
        user_info = retrive_data(email, password)
        login_window.destroy()
        page_template(main_window,user_info)
    else:
        print("Invalid login")





    



def Log_window(main_window):  
    main_window.withdraw()

    login_root = tk.Toplevel()
    login_root.title("Login")
    login_root.geometry("750x650")
    login_root.minsize(750, 650)
    login_root.configure(bg='#c9e4c4')

    # Navbar with "Back" button
    create_navbar(
        parent=login_root,
        logo_path="assets/Pams-logo.png",
        button_text="Back",
        button_command=lambda: [login_root.destroy(), main_window.deiconify()]
    )

    frame = tk.Frame(login_root, bg="#ffffff", width=400, height=350, relief="solid", border=1)
    frame.place(relx=0.5, rely=0.6, anchor="center")

    email_entry = create_entry(frame, 0, "Email", label_size=20)
    password_entry = create_entry(frame, 1, "Password", label_size=20, show="*")

    button_frame = tk.Frame(frame, bg="#ffffff")
    button_frame.grid(row=2, column=0, columnspan=2, pady=20)
    create_button(
        button_frame,
        text="Login",
        width=150,
        height=50,
        bg="red",
        fg="white",
        command=lambda: authentication(email_entry, password_entry, login_root, main_window)
    )

