import tkinter as tk
from core.helpers import create_button



def create_page(parent):
    frame = tk.Frame(parent, bg='#c9e4c4')

    # Top buttons frame (centered)
    top_btn_frame = tk.Frame(frame, bg='#c9e4c4')
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10))

    # Centering inner frame for buttons
    btns_inner_frame = tk.Frame(top_btn_frame, bg='#c9e4c4')
    btns_inner_frame.pack(anchor="center")

    btn_view_request = create_button(
        btns_inner_frame,
        text="view request",
        width=150,
        height=50,
        bg="#3B86FF",
        fg="white",
        command=None
    )
    btn_view_request.pack(side="left", padx=(0, 120))



    # Big box for apartments
    box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    placeholder_label = tk.Label(
        box_frame,
        text="requests will appear here",
        font=("Arial", 16),
        bg="white",
        fg="#888"
    )
    placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    return frame
