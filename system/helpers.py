import tkinter as tk

def create_button(parent,text="Click Me", width=150, height=50, bg="red",fg="white", command=None,x=None,y=None,next_window_func=None,current_window=None):
    """
    Creates a Tkinter Button and optionally makes it change pages.

    Parameters:
        parent (tk.Widget): Parent widget (usually the current window)
        text (str): Button text
        width, height (int): Button size
        bg, fg (str): Button colors
        command (function): Function to run on click
        x, y (int): Coordinates for placement
        next_window_func (function): Function that opens the next window
        current_window (tk.Tk or tk.Toplevel): The window to close when navigating
    """

    def on_click(event=None):
        if command:
            command()
        if next_window_func and current_window:
            current_window.destroy()
            next_window_func()

    # Get parent background color for canvas
    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else "white"
    # Create the canvas for button, set bg to parent bg
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0, bg=parent_bg)
    
    # Place or pack based on coordinates
    if x is not None and y is not None:
        canvas.place(x=x, y=y)
    else:
        canvas.pack(fill="x", expand=True, pady=5)

    # Draw rectangle and add tag for hover effect
    rect = canvas.create_rectangle(0, 0, width, height, fill=bg, outline=bg, tags="rect")
    label = canvas.create_text(width // 2, height // 2, text=text, fill=fg, font=("Arial", 14, "bold"))

    # Bind click events
    canvas.tag_bind("rect", "<Button-1>", on_click)
    canvas.tag_bind(label, "<Button-1>", on_click)

    # Hover effects
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
    # Navbar frame
    frame = tk.Frame(parent, bg="white", height=120)
    frame.pack(fill="x", padx=0, pady=(0, 30))
    frame.pack_propagate(False)

    # ---- Left frame for logo ----
    left_frame = tk.Frame(frame, bg="white")
    left_frame.pack(side="left", padx=20, pady=20)

    # Logo
    frame.logo_image = tk.PhotoImage(file=logo_path).subsample(2, 2)
    logo_lbl = tk.Label(left_frame, image=frame.logo_image, bg="white")
    logo_lbl.pack(side="left")

    # ---- Center frame for heading ----
    center_frame = tk.Frame(frame, bg="white")
    center_frame.pack(side="left", expand=True)  # expand=True keeps it centered

    heading = tk.Label(
        center_frame,
        text="Paragon Apartments",
        font=("Arial", 25, "bold"),
        bg="white"
    )
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



def create_side_navbar(parent, button_text,user_info, button_command=None):
    
    sidebar_width = 190
    frame = tk.Frame(parent, bg="white", width=sidebar_width)
    frame.pack(side="left", fill="y")
    frame.pack_propagate(False)

    # Force geometry to settle (prevents redraw glitches)
    frame.update()

    # Store buttons for collapse/expand
    frame.buttons = []

    # --- User info section at top ---
    user_info_frame = tk.Frame(frame, bg="white")
    user_info_frame.pack(side="top", fill="x", pady=(20, 10))

    # Placeholder for user image (replace with actual image as needed)
    user_img = tk.Label(user_info_frame, text="👤", font=("Arial", 30), bg="white")
    user_img.pack(side="top", pady=(0, 5))

    # Placeholder for user name and email (replace with actual values)
    user_name = tk.Label(user_info_frame, text=f"{user_info[1]} {user_info[2]}", font=("Arial", 12, "bold"), bg="white")
    user_name.pack(side="top")
    user_email = tk.Label(user_info_frame, text=f"{user_info[4]}", font=("Arial", 10), bg="white")
    user_email.pack(side="top")

    # --- Create buttons ---
    for i, text in enumerate(button_text):
        # Support list of commands
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

        # Reduce top padding for buttons
        btn.pack_configure(pady=(5 if i > 0 else 0))
        frame.buttons.append(btn)

    # --- Collapse / Expand logic ---
    collapsed = False

    def toggle_navbar():
        nonlocal collapsed
        collapsed = not collapsed

        # Resize frame
        frame.configure(width=50 if collapsed else sidebar_width)

        # Hide/show buttons
        # Hide/show user info
        if collapsed:
            user_img.pack_forget()
            user_name.pack_forget()
            user_email.pack_forget()
        else:
            user_img.pack(side="top", pady=(0, 5))
            user_name.pack(side="top")
            user_email.pack(side="top")

        # Hide/show buttons
        for btn in frame.buttons:
            if collapsed:
                btn.pack_forget()
            else:
                btn.pack(fill="x", expand=True, pady=10)

        # Update toggle arrow
        toggle_btn.configure(text="→" if collapsed else "←")

        # Force redraw (prevents shadow artifact)
        frame.update_idletasks()

    # --- Toggle button ---
    toggle_btn = tk.Button(
        frame,
        text="←",
        command=toggle_navbar,
        bg="#3B86FF",
        fg="white",
        bd=0,
        font=("Arial", 12, "bold")
    )
    toggle_btn.pack(side="bottom", fill="x", pady=5)

    return frame





def create_entry(parent, row, label_text, label_size, show=None):
    # Use a more Mac-friendly font and subtle border
    import platform
    system_font = "Helvetica Neue" if platform.system() == "Darwin" else "Arial"
    label = tk.Label(parent, text=label_text, font=(system_font, label_size), bg="#ffffff")
    label.grid(row=row, column=0, padx=25, pady=40, sticky="e")
    entry = tk.Entry(
        parent,
        show=show,
        font=(system_font, label_size),
        bg='white',
        bd=1,  # subtle border
        relief="groove",  # groove is more native on Mac
        highlightthickness=1,
        highlightbackground="#cccccc",
        highlightcolor="#3B86FF"
    )
    entry.grid(row=row, column=1, padx=25, pady=20, sticky="w", ipady=5)
    return entry
