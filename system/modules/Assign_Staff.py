import tkinter as tk
from tkinter import ttk, messagebox
from main.helpers import create_button


class AssignStaffPanel:

    def __init__(self, parent, request_id, on_submit=None, on_cancel=None):
        self.parent = parent
        self.request_id = request_id
        self.on_submit = on_submit
        self.on_cancel = on_cancel

        try:
            from database.maintaince_service import get_all_staff
            self._staff_list = get_all_staff() or []
        except Exception as e:
            self._staff_list = []
            messagebox.showerror("DB Error", f"Could not load staff list:\n{e}")

        self._render()

    def _render(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        tk.Label(
            wrapper,
            text=f"Assign Staff  —  Request #{self.request_id}",
            font=("Arial", 12, "bold"),
            bg="white", anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(
            wrapper, text="Staff Member:", font=("Arial", 10, "bold"),
            bg="white", anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)

        self._staff_names = [name for _, name in self._staff_list]
        self._staff_ids   = [eid  for eid, _ in self._staff_list]

        self.staff_dropdown = ttk.Combobox(
            wrapper,
            values=self._staff_names,
            state="readonly",
            width=28,
            font=("Arial", 10),
        )
        self.staff_dropdown.grid(row=1, column=1, sticky="w", pady=4)
        if self._staff_names:
            self.staff_dropdown.current(0)

        tk.Label(
            wrapper, text="Notes:", font=("Arial", 10, "bold"),
            bg="white", anchor="nw",
        ).grid(row=2, column=0, sticky="nw", padx=(0, 10), pady=4)

        self.notes_text = tk.Text(
            wrapper, width=40, height=3, font=("Arial", 10), wrap="word",
        )
        self.notes_text.grid(row=2, column=1, sticky="w", pady=4)

        wrapper.grid_columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))

        for text, bg, cmd, w in [
            ("Assign", "#3B86FF", self._submit,                                        140),
            ("Cancel", "#6c757d", self.on_cancel if self.on_cancel else lambda: None,  100),
        ]:
            create_button(
                btn_frame, text=text, width=w, height=45,
                bg=bg, fg="white", command=cmd,
                next_window_func=None, current_window=None,
            ).pack(side="left", padx=(0, 8))

    def _submit(self):
        staff_name = self.staff_dropdown.get().strip()
        notes      = self.notes_text.get("1.0", "end").strip()

        if not staff_name:
            messagebox.showerror("Validation Error", "Please select a staff member.")
            return

        try:
            employee_id = self._staff_ids[self._staff_names.index(staff_name)]
        except ValueError:
            messagebox.showerror("Error", "Selected staff member not found.")
            return

        try:
            from database.maintaince_service import assign_staff
            result = assign_staff(self.request_id, employee_id, notes or None)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not assign staff:\n{e}")
            return

        if result:
            if self.on_submit:
                self.on_submit(self.request_id, staff_name)
        else:
            messagebox.showerror("Error", "Assignment failed — no rows were updated.")