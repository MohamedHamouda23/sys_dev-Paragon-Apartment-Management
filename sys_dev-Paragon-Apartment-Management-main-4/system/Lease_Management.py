import tkinter as tk



def create_page(parent):
    frame = tk.Frame(parent, bg='#c9e4c4')

    # Top buttons frame
    top_btn_frame = tk.Frame(frame, bg='#c9e4c4')
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10), padx=30)

    btn_add_lease= tk.Button(top_btn_frame, text="Add lease", font=("Arial", 12, "bold"), width=15, height=2, bg="#3B86FF", fg="white")
    btn_add_lease.pack(side="left", padx=(0, 20))

    btn_track_lease = tk.Button(top_btn_frame, text="Track lease", font=("Arial", 12, "bold"), width=15, height=2, bg="#3B86FF", fg="white")
    btn_track_lease.pack(side="left")
    
    btn_remove_lease = tk.Button(top_btn_frame, text="Remove lease", font=("Arial", 12, "bold"), width=15, height=2, bg="#3B86FF", fg="white")
    btn_remove_lease.pack(side="right")

    box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    placeholder_label = tk.Label(
        box_frame,
        text="Registered lease will appear here",
        font=("Arial", 16),
        bg="white",
        fg="#888"
    )
    placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    return frame
