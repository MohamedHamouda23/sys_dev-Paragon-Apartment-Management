import tkinter as tk
from main.helpers import create_window, create_navbar
from main.log_in import Log_window
def main_window():
    root = create_window("Paragon Apartments Management System")
    root.icon_image = tk.PhotoImage(master=root, file="assets/Pams-logo.png").subsample(2, 2)
    root.iconphoto(True, root.icon_image)

    # ---- NAVBAR ----
    create_navbar(
        parent=root,
        logo_path="assets/Pams-logo.png",
        button_text="Log In",
        button_command=lambda: Log_window(root)  # pass main window
    )

    # ---- MAIN IMAGE ----
    root.main_img = tk.PhotoImage(master=root, file="assets/main.png").subsample(2, 2)
    tk.Label(root, image=root.main_img, bg="#c9e4c4").pack(pady=15)

    # ---- DESCRIPTION ----
    tk.Label(
        root,
        text=("2 BED • 2 BATH • 1,150 SQ FT • BUILT 2018\n"
              "PRIVATE BALCONY • COMMUNAL GARDENS\n"
              "3-MIN WALK TO HIGH ST KENSINGTON\n"
              "ON-SITE GYM • CONCIERGE • SECURE PARKING"),
        font=("Arial", 11, "bold"),  
        bg="#c9e4c4", justify="center", fg="#2c3e50"
    ).pack(pady=10)

    # ---- GALLERY ----
    gallery = tk.Frame(root, bg="#c9e4c4")
    gallery.pack(pady=20, padx=20)

    root.gallery_images = []

    images = [
        ("assets/image2.gif",
         "2 BED • 2 BATH • 980 SQ FT • BUILT 2020\n"
         "PANORAMIC CITY VIEWS\n"
         "RESIDENTS SPA & POOL\n"
         "PARKING • 24/7 SECURITY", 1),

        ("assets/image1.gif",
         "2 BED • 1 BATH • 890 SQ FT • BUILT 2017\n"
         "BRISTOL HARBOURSIDE VIEWS\n"
         "RIVERSIDE WALKING PATH\n"
         "MODERN KITCHEN • LIFT ACCESS", 4),

        ("assets/image3.gif",
         "2 BED • 2 BATH • 1,050 SQ FT • BUILT 2019\n"
         "PRIVATE BALCONY VIEWS\n"
         "COMMUNAL GARDENS\n"
         "CONCIERGE • GYM ACCESS", 1)
    ]

    for img_file, desc, subsample_size in images:
        card = tk.Frame(gallery, bg="#c9e4c4")
        card.pack(side="left", padx=15)

        try:
            img = tk.PhotoImage(master=root, file=img_file).subsample(subsample_size, subsample_size)
        except tk.TclError:
            print(f"Cannot load image: {img_file}")
            continue

        root.gallery_images.append(img)
        tk.Label(card, image=img, bg="#c9e4c4").pack(pady=(10, 5), padx=30)
        tk.Label(
            card,
            text=desc,
            font=("Arial", 9, "bold"),  
            bg="#c9e4c4", justify="center", fg="#2c3e50"
        ).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main_window()
