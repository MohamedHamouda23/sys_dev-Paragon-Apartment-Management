import tkinter as tk
import platform  
from tkinter import ttk

# -------------------------------------------------------
# Constants
# -------------------------------------------------------
BG         = "white"
ACCENT     = "#E53935"
BTN_FG     = "white"
FONT_TITLE = ("Arial", 20, "bold")
FONT_LABEL = ("Arial", 12)
FONT_ENTRY = ("Arial", 12)
FONT_BTN   = ("Arial", 12, "bold")
ENTRY_H    = 36
ENTRY_W    = 28
RADIUS     = 6
NAV_BG     = BG          
APP_BG     = '#c9e4c4'
NAV_BTN    = "#3B86FF"


# -------------------------------------------------------
# Core Widgets
# -------------------------------------------------------

def create_button(parent, text="Click Me", width=150, height=50, bg="red", fg=BTN_FG,
                  command=None, x=None, y=None, next_window_func=None, current_window=None):
    """Improved styled canvas button with persistent hover states."""
    def on_click(event=None):
        if command:
            command()
        if next_window_func and current_window:
            current_window.destroy()
            next_window_func()

    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else BG
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0, bg=parent_bg)

    canvas.base_color = bg

    if x is not None and y is not None:
        canvas.place(x=x, y=y)
    else:
        canvas.pack(fill="x", expand=True, pady=5)

    canvas.create_rectangle(0, 0, width, height, fill=bg, outline=bg, tags="rect")
    canvas.create_text(width // 2, height // 2, text=text, fill=fg, font=("Arial", 14, "bold"), tags="text")

    def on_enter(e):
        if canvas.base_color in ("white", NAV_BG):
            h_color = "#dbeafe"   # more visible than #f0f0f0
        elif canvas.base_color in ("red", "#E53935"):
            h_color = "#cc0000"
        elif canvas.base_color == NAV_BTN:
            h_color = "#2a62c9"
        else:
            h_color = canvas.base_color
        canvas.itemconfig("rect", fill=h_color, outline=h_color)

    def on_leave(e):
        canvas.itemconfig("rect", fill=canvas.base_color, outline=canvas.base_color)

    canvas.tag_bind("rect", "<Button-1>", on_click)
    canvas.tag_bind("text", "<Button-1>", on_click)

    canvas.tag_bind("rect", "<Enter>", on_enter)
    canvas.tag_bind("text", "<Enter>", on_enter)
    canvas.tag_bind("rect", "<Leave>", on_leave)
    canvas.tag_bind("text", "<Leave>", on_leave)

    return canvas

def create_window(title):
    root = tk.Tk()
    root.title(title)
    root.geometry("750x650")
    root.minsize(750, 650)
    root.configure(bg=APP_BG)
    return root


def create_frame(parent):
    frame = tk.Frame(parent, bg=APP_BG)
    top_btn_frame = tk.Frame(frame, bg=APP_BG)
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10))
    btns_inner_frame = tk.Frame(top_btn_frame, bg=APP_BG)
    btns_inner_frame.pack(anchor="center")
    box_frame = tk.Frame(frame, bg=APP_BG)
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))
    return frame, btns_inner_frame, box_frame


def clear_frame(frame):
    """Remove all widgets inside a given frame."""
    for widget in frame.winfo_children():
        widget.destroy()


# -------------------------------------------------------
# Navigation
# -------------------------------------------------------

def _nav_frame(parent, bg=NAV_BG, **pack_kwargs):
    """Shared helper: creates a white sub-frame inside a navbar."""
    f = tk.Frame(parent, bg=bg)
    f.pack(**pack_kwargs)
    return f


def create_navbar(parent, logo_path, button_text, button_command=None):
    frame = tk.Frame(parent, bg=NAV_BG, height=120)
    frame.pack(fill="x", padx=0, pady=(0, 30))
    frame.pack_propagate(False)

    left_frame = _nav_frame(frame, side="left", padx=20, pady=20)
    frame.logo_image = tk.PhotoImage(master=frame, file=logo_path).subsample(2, 2)
    tk.Label(left_frame, image=frame.logo_image, bg=NAV_BG).pack(side="left")

    center_frame = _nav_frame(frame, side="left", expand=True)
    tk.Label(center_frame, text="Paragon Apartments", font=("Arial", 25, "bold"), bg=NAV_BG).pack()

    right_frame = _nav_frame(frame, side="right", padx=20, pady=20)
    create_button(right_frame, text=button_text, width=150, height=50,
                  bg=NAV_BTN, fg=BTN_FG, command=button_command,
                  current_window=parent).pack()

    return frame


def create_side_navbar(parent, button_text, user_info, button_command=None):
    sidebar_width = 190
    collapsed_width = 50
    collapsed = False 

    frame = tk.Frame(parent, bg=NAV_BG, width=sidebar_width)
    frame.pack(side="left", fill="y")
    frame.pack_propagate(False)

    # 1. Logout Logic
    def logout_command():
        logout_page(frame, parent)

    # Info section
    info_frame = _nav_frame(frame, side="top", fill="x", pady=(20, 10))
    tk.Label(info_frame, text="👤", font=("Arial", 30), bg=NAV_BG).pack(side="top", pady=(0, 5))
    tk.Label(info_frame, text=f"{user_info[1]} {user_info[2]} ({user_info[3]})", 
             font=("Arial", 12, "bold"), bg=NAV_BG).pack(side="top")
    tk.Label(info_frame, text=f"{user_info[4]}", font=("Arial", 10), bg=NAV_BG).pack(side="top")

    # 2. Middle Container (Spreads the middle buttons)
    nav_container = tk.Frame(frame, bg=NAV_BG)
    
    nav_buttons = []
    for i, text in enumerate(button_text):
        if text.strip().lower() == "logout": continue
        cmd = button_command[i] if isinstance(button_command, list) else button_command
        btn = create_button(nav_container, text=text, width=sidebar_width, height=50,
                           bg=NAV_BG, fg="black", command=cmd, current_window=parent)
        nav_buttons.append(btn)

    # 3. Footer Buttons
    # Added command=logout_command here to make it work
    logout_btn = create_button(frame, text="Logout", width=sidebar_width, height=40,
                               bg="#E53935", fg="white", command=logout_command, 
                               current_window=parent)
    
    toggle_btn = create_button(frame, text="←", width=sidebar_width, height=40,
                               bg=NAV_BTN, fg=BTN_FG)

    def _apply_sidebar_state():
        nonlocal collapsed
        current_w = collapsed_width if collapsed else sidebar_width
        frame.configure(width=current_w)

        # Clear layout to re-draw
        info_frame.pack_forget()
        nav_container.pack_forget()
        for btn in nav_buttons: btn.pack_forget()
        logout_btn.pack_forget()
        toggle_btn.pack_forget()

        # Update widths and CENTER text/rect for all buttons
        for b in nav_buttons + [logout_btn, toggle_btn]:
            h = 50 if b in nav_buttons else 40
            b.config(width=current_w)
            b.coords("rect", 0, 0, current_w, h)
            b.coords("text", current_w // 2, h // 2)

        # --- PACKING LOGIC ---
        toggle_btn.pack(side="bottom", fill="x")
        logout_btn.pack(side="bottom", fill="x")

        if not collapsed:
            info_frame.pack(side="top", fill="x", pady=(20, 10))
            nav_container.pack(side="top", fill="both", expand=True)
            for btn in nav_buttons:
                btn.pack(side="top", fill="x", expand=True)
            
            logout_btn.itemconfig("text", text="Logout")
            toggle_btn.itemconfig("text", text="←")
        else:
            logout_btn.itemconfig("text", text="")
            toggle_btn.itemconfig("text", text="→")

    toggle_btn.tag_bind("rect", "<Button-1>", lambda e: do_toggle())
    toggle_btn.tag_bind("text", "<Button-1>", lambda e: do_toggle())

    def do_toggle():
        nonlocal collapsed
        collapsed = not collapsed
        _apply_sidebar_state()

    _apply_sidebar_state()
    return frame
    

# --- Rest of the helper functions unchanged ---

def styled_label(parent, text, font=FONT_LABEL, fg="#333333"):
    return tk.Label(parent, text=text, font=font, bg=BG, fg=fg)

def styled_entry(parent):
    frame = tk.Frame(parent, bg="#E0E0E0", bd=0)
    inner = tk.Frame(frame, bg=BG, padx=2, pady=2)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    e = tk.Entry(inner, font=FONT_ENTRY, bg=BG, relief="flat",
                 fg="#222", insertbackground="#222", width=ENTRY_W)
    e.pack(fill="both", ipady=8)
    return frame, e

def styled_dropdown(parent, values):
    style = ttk.Style()
    style.configure("Flat.TCombobox", fieldbackground=BG, background=BG,
                    foreground="#222", arrowsize=14, padding=6)
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      state="readonly", width=ENTRY_W, font=FONT_ENTRY,
                      style="Flat.TCombobox")
    return cb, var

def _form_label(container, label_text):
    styled_label(container, label_text, fg="#555").pack(anchor="w", pady=(10, 2))

def create_entry(parent, row, label_text, label_size, show=None):
    system_font = "Helvetica Neue" if platform.system() == "Darwin" else "Arial"
    tk.Label(parent, text=label_text, font=(system_font, label_size), bg=BG).grid(
        row=row, column=0, padx=25, pady=40, sticky="e")
    entry = tk.Entry(parent, show=show, font=(system_font, label_size),
                     bg=BG, bd=1, relief="groove",
                     highlightthickness=1, highlightbackground="#cccccc",
                     highlightcolor=NAV_BTN)
    entry.grid(row=row, column=1, padx=25, pady=20, sticky="w", ipady=5)
    return entry

def form_field(container, label_text, row_tracker=None):
    _form_label(container, label_text)
    border, entry = styled_entry(container)
    border.pack(fill="x")
    return entry

def form_dropdown(container, label_text, values):
    _form_label(container, label_text)
    cb, var = styled_dropdown(container, values)
    cb.pack(fill="x", ipady=4)
    return cb

def card(parent):
    shadow = tk.Frame(parent, bg="#D0D0D0")
    shadow.place(relx=0.5, rely=0.5, anchor="center")
    inner = tk.Frame(shadow, bg=BG, padx=32, pady=28)
    inner.pack(padx=2, pady=2)
    return inner

def logout_page(current_frame, parent_widget):
    try:
        root = parent_widget.winfo_toplevel()
        if root: root.destroy()
        from main.index import main_window
        main_window()
    except Exception as e:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Logout Error", f"Could not return to index page: {e}")

def create_logout_button(parent_frame, target_frame, parent_widget, anchor="ne", padx=10, pady=0):
    from main.helpers import logout_page
    btn = create_button(
        parent_frame,
        text="➜]",
        width=35,
        height=35,
        bg="#FF3B3B",
        fg="white",
        command=lambda: logout_page(target_frame, parent_widget.winfo_toplevel()),
    )
    btn.pack(anchor=anchor, padx=padx, pady=pady)
    return btn

def create_scrollable_treeview(parent, columns, headings, widths, anchors, height=9):
    table_wrap = tk.Frame(parent, bg="white", bd=2, relief="groove")
    table_wrap.pack(fill="both", expand=True, pady=(0, 12))
    tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=height)
    for col, heading, width, anchor in zip(columns, headings, widths, anchors):
        tree.heading(col, text=heading)
        tree.column(col, width=width, anchor=anchor)
    y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=y_scroll.set)
    tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))
    return table_wrap, tree

def reset_combobox(combobox, names):
    combobox.set(names[0] if names else "")

def show_placeholder(parent, text=""):
    for widget in parent.winfo_children():
        widget.destroy()
    tk.Label(
        parent,
        text=text,
        bg="white",
        fg="#888888",
        font=("Arial", 10, "italic"),
        pady=16,
    ).pack(expand=True)