import tkinter as tk




def create_page(parent):
    frame = tk.Frame(parent, bg='#c9e4c4')

    label = tk.Label(
        frame,
        text="This is the Users page",
        font=("Arial", 24)
    )
    label.pack(expand=True)

    return frame
