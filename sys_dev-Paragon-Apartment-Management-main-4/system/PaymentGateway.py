# Log_in.py
import tkinter as tk
from helpers import create_button, create_entry, create_navbar
from Dashbaord import page_template 

def payment_window(main_window):
    main_window.withdraw()

    payment_root = tk.Toplevel()
    payment_root.title("Secure Payment")
    payment_root.geometry("750x650")
    payment_root.minsize(750, 650)
    payment_root.configure(bg='#c9e4c4')




  

    # --- CARD FORM FRAME ---
    frame = tk.Frame(payment_root, bg="#ffffff", width=400, height=500,
                    relief="solid", borderwidth=1)
    frame.place(relx=0.5, rely=0.55, anchor="center")

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)


    amount_entry = tk.Entry(frame, font=("Arial", 14), justify="center")
    amount_entry.grid(
        row=1,
        column=0,
        columnspan=2,
        pady=(20, 15),
        ipadx=40,   # controls width
        ipady=6
    )


    # ---- Cardholder ----
    cardholder_label = tk.Label(frame, text="Cardholder Name", font=("Arial", 14), bg="#ffffff")
    cardholder_label.grid(row=2, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")

    cardholder_entry = tk.Entry(frame, font=("Arial", 14))
    cardholder_entry.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10),
                        sticky="ew", ipadx=10, ipady=5)

    # ---- Card number ----
    card_number_label = tk.Label(frame, text="Card Number", font=("Arial", 14), bg="#ffffff")
    card_number_label.grid(row=4, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")

    card_number_entry = tk.Entry(frame, font=("Arial", 14))
    card_number_entry.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10),
                        sticky="ew", ipadx=10, ipady=5)

    # ---- CVC + Expiry ----
    cvc_label = tk.Label(frame, text="CVC", font=("Arial", 14), bg="#ffffff")
    cvc_label.grid(row=6, column=0, padx=10, pady=(10, 0), sticky="w")

    cvc_entry = tk.Entry(frame, font=("Arial", 14))
    cvc_entry.grid(row=7, column=0, padx=10, pady=(0, 10),
                sticky="ew", ipadx=10, ipady=5)

    expiry_label = tk.Label(frame, text="Expiry Date (MM/YY)", font=("Arial", 14), bg="#ffffff")
    expiry_label.grid(row=6, column=1, padx=10, pady=(10, 0), sticky="w")

    expiry_entry = tk.Entry(frame, font=("Arial", 14))
    expiry_entry.grid(row=7, column=1, padx=10, pady=(0, 10),
                    sticky="ew", ipadx=10, ipady=5)

    # ---- Buttons ----
    button_frame1 = tk.Frame(frame, bg="#ffffff")
    button_frame1.grid(row=8, column=0, pady=20)

    button_frame2 = tk.Frame(frame, bg="#ffffff")
    button_frame2.grid(row=8, column=1, pady=20)



    create_button(
        button_frame1,
        text="Cancel",
        width=150,
        height=50,
        bg="white",            
        fg="red",               
            

    )


    create_button(
        button_frame2,
        text="Pay Now",
        width=150,
        height=50,
        bg="red",
        fg="white",
        command=lambda: validate(card_number_entry, cvc_entry, payment_root, cardholder_entry, main_window)
    )
