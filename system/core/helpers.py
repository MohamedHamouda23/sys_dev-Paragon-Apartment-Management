import tkinter as tk
import platform  

def create_button(parent, text="Click Me", width=150, height=50, bg="red", fg="white",
                  command=None, x=None, y=None, next_window_func=None, current_window=None):
    """
    Creates a Tkinter Button and optionally makes it change pages.
    """
    def on_click(event=None):
        if command:
            command()
        if next_window_func and current_window:
            current_window.destroy()
            next_window_func()

    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else "white"
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0, bg=parent_bg)

    if x is not None and y is not None:
        canvas.place(x=x, y=y)
    else:
        canvas.pack(fill="x", expand=True, pady=5)

    rect = canvas.create_rectangle(0, 0, width, height, fill=bg, outline=bg, tags="rect")
    label = canvas.create_text(width // 2, height // 2, text=text, fill=fg, font=("Arial", 14, "bold"))

    canvas.tag_bind("rect", "<Button-1>", on_click)
    canvas.tag_bind(label, "<Button-1>", on_click)

    def on_enter(event):
        canvas.itemconfig("rect", fill="#cc0000" if bg == "red" else "#666")

    def on_leave(event):
        canvas.itemconfig("rect", fill=bg)

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)

    return canvas


def create_window(title):
    root = tk.Tk()
    root.title(title)
    root.geometry("750x650")
    root.minsize(750, 650)
    root.configure(bg='#c9e4c4')
    return root


def create_navbar(parent, logo_path, button_text, button_command=None):
    frame = tk.Frame(parent, bg="white", height=120)
    frame.pack(fill="x", padx=0, pady=(0, 30))
    frame.pack_propagate(False)

    left_frame = tk.Frame(frame, bg="white")
    left_frame.pack(side="left", padx=20, pady=20)

    frame.logo_image = tk.PhotoImage(file=logo_path).subsample(2, 2)
    logo_lbl = tk.Label(left_frame, image=frame.logo_image, bg="white")
    logo_lbl.pack(side="left")

    center_frame = tk.Frame(frame, bg="white")
    center_frame.pack(side="left", expand=True)
    heading = tk.Label(center_frame, text="Paragon Apartments", font=("Arial", 25, "bold"), bg="white")
    heading.pack()

    right_frame = tk.Frame(frame, bg="white")
    right_frame.pack(side="right", padx=20, pady=20)

    create_button(
        right_frame,
        text=button_text,
        width=150,
        height=50,
        bg="#3B86FF",
        fg="white",
        command=button_command,
        next_window_func=None,
        current_window=parent
    ).pack()

    return frame


def create_side_navbar(parent, button_text, user_info, button_command=None):
    sidebar_width = 190
    frame = tk.Frame(parent, bg="white", width=sidebar_width)
    frame.pack(side="left", fill="y")
    frame.pack_propagate(False)
    frame.update()

    frame.buttons = []

    user_info_frame = tk.Frame(frame, bg="white")
    user_info_frame.pack(side="top", fill="x", pady=(20, 10))

    user_img = tk.Label(user_info_frame, text="👤", font=("Arial", 30), bg="white")
    user_img.pack(side="top", pady=(0, 5))

    user_name = tk.Label(user_info_frame, text=f"{user_info[1]} {user_info[2]}", font=("Arial", 12, "bold"), bg="white")
    user_name.pack(side="top")
    user_email = tk.Label(user_info_frame, text=f"{user_info[4]}", font=("Arial", 10), bg="white")
    user_email.pack(side="top")

    for i, text in enumerate(button_text):
        cmd = button_command[i] if isinstance(button_command, list) else button_command
        btn = create_button(
            frame,
            text=text,
            width=sidebar_width,
            height=50,
            bg="white",
            fg="black",
            command=cmd,
            next_window_func=None,
            current_window=parent
        )
        btn.pack_configure(pady=(5 if i > 0 else 0))
        frame.buttons.append(btn)

    collapsed = False

    def toggle_navbar():
        nonlocal collapsed
        collapsed = not collapsed
        frame.configure(width=50 if collapsed else sidebar_width)
        if collapsed:
            user_img.pack_forget()
            user_name.pack_forget()
            user_email.pack_forget()
        else:
            user_img.pack(side="top", pady=(0, 5))
            user_name.pack(side="top")
            user_email.pack(side="top")

        for btn in frame.buttons:
            if collapsed:
                btn.pack_forget()
            else:
                btn.pack(fill="x", expand=True, pady=10)

        toggle_btn.configure(text="→" if collapsed else "←")
        frame.update_idletasks()

    toggle_btn = tk.Button(frame, text="←", command=toggle_navbar, bg="#3B86FF", fg="white",
                           bd=0, font=("Arial", 12, "bold"))
    toggle_btn.pack(side="bottom", fill="x", pady=5)

    return frame


def create_entry(parent, row, label_text, label_size, show=None):
    system_font = "Helvetica Neue" if platform.system() == "Darwin" else "Arial"
    label = tk.Label(parent, text=label_text, font=(system_font, label_size), bg="#ffffff")
    label.grid(row=row, column=0, padx=25, pady=40, sticky="e")
    entry = tk.Entry(parent, show=show, font=(system_font, label_size),
                     bg='white', bd=1, relief="groove",
                     highlightthickness=1, highlightbackground="#cccccc", highlightcolor="#3B86FF")
    entry.grid(row=row, column=1, padx=25, pady=20, sticky="w", ipady=5)
    return entry


def styled_button(parent, **kwargs):
    return tk.Button(parent, font=("Arial", 12, "bold"), bg="#3B86FF", fg="white",
                     relief="raised", bd=2, padx=10, pady=4,
                     activebackground="#1c5db6", activeforeground="white",
                     cursor="hand2", **kwargs)


def create_frame(parent):
    frame = tk.Frame(parent, bg='#c9e4c4')
    top_btn_frame = tk.Frame(frame, bg='#c9e4c4')
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10))
    btns_inner_frame = tk.Frame(top_btn_frame, bg='#c9e4c4')
    btns_inner_frame.pack(anchor="center")
    box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))
    return frame, btns_inner_frame, box_frame


def clear_frame(frame):
        """Remove all widgets inside a given frame."""
        for widget in frame.winfo_children():
            widget.destroy()

