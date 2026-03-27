import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_button
from database.tenant_portal_service import get_tenant_complaints, submit_tenant_complaint

def create_page(parent, user_info=None):
    frame = tk.Frame(parent, bg='#c9e4c4')
    role = user_info[4] if user_info and len(user_info) > 4 else None
    user_id = user_info[0] if user_info else None

    if role != "Tenant":
        box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
        box_frame.pack(fill="both", expand=True, padx=40, pady=(20, 40))
        tk.Label(
            box_frame,
            text="Complaints page is tenant-facing in this view.",
            bg="white",
            font=("Arial", 14, "bold"),
            fg="#1f3b63",
        ).pack(expand=True)
        return frame

    # Top buttons frame (centered)
    top_btn_frame = tk.Frame(frame, bg='#c9e4c4')
    top_btn_frame.pack(side="top", fill="x", pady=(30, 10))

    # Centering inner frame for buttons
    btns_inner_frame = tk.Frame(top_btn_frame, bg='#c9e4c4')
    btns_inner_frame.pack(anchor="center")

    form_box = tk.Frame(btns_inner_frame, bg="#c9e4c4")
    form_box.pack(anchor="center")

    tk.Label(form_box, text="Complaint", bg="#c9e4c4", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=6, pady=4, sticky="w")
    description_entry = tk.Entry(form_box, width=42)
    description_entry.grid(row=0, column=1, padx=6, pady=4)

    def load_complaints():
        tree.delete(*tree.get_children())
        for row in get_tenant_complaints(user_id):
            # Your table only has 3 columns: complaint_id, description, date_submitted
            complaint_id, description, date_submitted = row
            tree.insert("", "end", values=(complaint_id, description, date_submitted))

    def submit_complaint():
        description = description_entry.get().strip()
        if not description:
            messagebox.showerror("Validation Error", "Complaint text is required.")
            return
        try:
            # Ensure this call matches the modified service function above
            submit_tenant_complaint(user_id, description) 
            description_entry.delete(0, tk.END)
            load_complaints()
            messagebox.showinfo("Success", "Complaint submitted.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit: {e}")

    tk.Button(
        form_box,
        text="Submit Complaint",
        command=submit_complaint,
        bg="#3B86FF",
        fg="white",
        font=("Arial", 10, "bold"),
        relief="flat",
        padx=12,
        pady=6,
    ).grid(row=0, column=2, padx=6, pady=4)

    # Big box for complaints list
    box_frame = tk.Frame(frame, bg="white", bd=2, relief="groove")
    box_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))

    # Updated columns to match your table structure
    columns = ("id", "description", "date")
    tree = ttk.Treeview(box_frame, columns=columns, show="headings", height=16)

    tree.heading("id", text="Complaint ID")
    tree.heading("description", text="Complaint Description")
    tree.heading("date", text="Date Submitted")

    tree.column("id", width=100, anchor="center")
    tree.column("description", width=500, anchor="w")
    tree.column("date", width=150, anchor="center")

    y_scroll = ttk.Scrollbar(box_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=y_scroll.set)

    tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    y_scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

    load_complaints()

    frame.on_show = load_complaints
    return frame