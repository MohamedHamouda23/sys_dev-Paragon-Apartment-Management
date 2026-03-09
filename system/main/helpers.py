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
    """Creates a styled canvas button with hover effect and optional page navigation."""
    def on_click(event=None):
        if command:
            command()
        if next_window_func and current_window:
            current_window.destroy()
            next_window_func()

    parent_bg = parent.cget("bg") if hasattr(parent, "cget") else BG
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0, bg=parent_bg)

    if x is not None and y is not None:
        canvas.place(x=x, y=y)
    else:
        canvas.pack(fill="x", expand=True, pady=5)

    canvas.create_rectangle(0, 0, width, height, fill=bg, outline=bg, tags="rect")
    label = canvas.create_text(width // 2, height // 2, text=text, fill=fg, font=("Arial", 14, "bold"))

    hover_color = "#cc0000" if bg == "red" else "#666"
    canvas.tag_bind("rect", "<Button-1>", on_click)
    canvas.tag_bind(label,  "<Button-1>", on_click)
    canvas.bind("<Enter>", lambda e: canvas.itemconfig("rect", fill=hover_color))
    canvas.bind("<Leave>", lambda e: canvas.itemconfig("rect", fill=bg))

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
    frame = tk.Frame(parent, bg=NAV_BG, width=sidebar_width)
    frame.pack(side="left", fill="y")
    frame.pack_propagate(False)
    frame.update()
    frame.buttons = []

    # Footer controls area keeps bottom controls stable.
    footer_frame = tk.Frame(frame, bg=NAV_BG)
    footer_frame.pack(side="bottom", fill="x", pady=(0, 10))

    def logout_command():
        logout_page(frame, parent)

    logout_btn = create_button(
        footer_frame,
        text="Logout",
        width=sidebar_width,
        height=36,
        bg="#E53935",
        fg="white",
        command=logout_command,
        current_window=parent,
    )

    # User info section
    info_frame = _nav_frame(frame, side="top", fill="x", pady=(20, 10))
    user_img   = tk.Label(info_frame, text="👤", font=("Arial", 30), bg=NAV_BG)
    user_name  = tk.Label(info_frame, text=f"{user_info[1]} {user_info[2]}", font=("Arial", 12, "bold"), bg=NAV_BG)
    user_email = tk.Label(info_frame, text=f"{user_info[4]}", font=("Arial", 10), bg=NAV_BG)
    for widget, kw in [(user_img, {"pady": (0, 5)}), (user_name, {}), (user_email, {})]:
        widget.pack(side="top", **kw)

    # Sidebar navigation buttons (excluding logout)

    nav_buttons = []
    # Only add navigation buttons (no logout)
    for i, text in enumerate(button_text):
        if text.strip().lower() == "logout":
            continue
        cmd = button_command[i] if isinstance(button_command, list) else button_command
        btn = create_button(frame, text=text, width=sidebar_width, height=50,
                           bg=NAV_BG, fg="black", command=cmd, current_window=parent)
        btn.pack_configure(pady=(5 if i > 0 else 0))
        nav_buttons.append(btn)
        frame.buttons.append(btn)

    collapsed = False

    def toggle_navbar():
        nonlocal collapsed
        collapsed = not collapsed
        frame.configure(width=50 if collapsed else sidebar_width)
        info_widgets = [user_img, user_name, user_email]
        if collapsed:
            for w in info_widgets: w.pack_forget()
            for btn in nav_buttons: btn.pack_forget()
            logout_btn.pack_forget()
        else:
            user_img.pack(side="top", pady=(0, 5))
            for w in [user_name, user_email]: w.pack(side="top")
            for btn in nav_buttons: btn.pack(fill="x", expand=True, pady=10)
            logout_btn.pack(side="top", fill="x", pady=(0, 2), before=toggle_btn)
        toggle_btn.configure(text="→" if collapsed else "←")
        frame.update_idletasks()

    # Place nav buttons at the top
    for btn in nav_buttons:
        btn.pack(fill="x", expand=True, pady=10)

    # Place footer buttons with deterministic order: logout above collapse.
    toggle_btn = tk.Button(footer_frame, text="←", command=toggle_navbar,
                           bg=NAV_BTN, fg=BTN_FG, bd=0, font=FONT_BTN)
    toggle_btn.pack(side="top", fill="x", pady=(0, 0))
    logout_btn.pack(side="top", fill="x", pady=(0, 2), before=toggle_btn)

    return frame




def styled_label(parent, text, font=FONT_LABEL, fg="#333333"):
    """A clean label with consistent styling."""
    return tk.Label(parent, text=text, font=font, bg=BG, fg=fg)


def styled_entry(parent):
    """A full-height, bordered entry widget."""
    frame = tk.Frame(parent, bg="#E0E0E0", bd=0)
    inner = tk.Frame(frame, bg=BG, padx=2, pady=2)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    e = tk.Entry(inner, font=FONT_ENTRY, bg=BG, relief="flat",
                 fg="#222", insertbackground="#222", width=ENTRY_W)
    e.pack(fill="both", ipady=8)
    return frame, e


def styled_dropdown(parent, values):
    """A styled combobox matching entry height."""
    style = ttk.Style()
    style.configure("Flat.TCombobox", fieldbackground=BG, background=BG,
                    foreground="#222", arrowsize=14, padding=6)
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      state="readonly", width=ENTRY_W, font=FONT_ENTRY,
                      style="Flat.TCombobox")
    return cb, var


def _form_label(container, label_text):
    """Shared label rendering used by form_field and form_dropdown."""
    styled_label(container, label_text, fg="#555").pack(anchor="w", pady=(10, 2))


def create_entry(parent, row, label_text, label_size, show=None):
    """Grid-based label + entry (used in login/register screens)."""
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
    """Adds a label + entry pair, returns the entry widget."""
    _form_label(container, label_text)
    border, entry = styled_entry(container)
    border.pack(fill="x")
    return entry


def form_dropdown(container, label_text, values):
    """Adds a label + combobox pair, returns the combobox widget."""
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
    """
    Log out the current user and return to the index page.
    """
    try:
        root = parent_widget.winfo_toplevel()
    except Exception:
        root = None

    try:
        if root:
            root.destroy()
    except Exception:
        pass

    try:
        from main.index import main_window
        main_window()
    except Exception as e:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Logout Error", f"Could not return to index page: {e}")

        messagebox.showerror("Logout Error", f"Could not show login page: {e}")

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
        next_window_func=None,
        current_window=None
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
    """
    Set a combobox to its first item, or clear it if the list is empty.

    Parameters
    ----------
    combobox : ttk.Combobox
    names    : list[str]  – the current values list
    """
    combobox.set(names[0] if names else "")



def show_placeholder(parent, text=""):
    """Clear a frame and display a centred placeholder message."""
    for widget in parent.winfo_children():
        widget.destroy()
    import tkinter as tk
    tk.Label(
        parent,
        text=text,
        bg="white",
        fg="#888888",
        font=("Arial", 10, "italic"),
        pady=16,
    ).pack(expand=True)