# ============================================================================
# LIFECYCLE MANAGEMENT MODULE
# Handles staff assignment, scheduling, and request resolution
# ============================================================================

import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from main.helpers import create_button
from validations import validate_staff_assignment, validate_resolution_form


# ============================================================================
# STAFF ASSIGNMENT PANEL
# ============================================================================

class StaffAssignmentPanel:
    """Combined staff assignment and scheduling with 3 fixed time slots per day"""
    
    TIME_SLOTS = ["09:00", "13:00", "17:00"]
    
    def __init__(self, parent, request_id, tenant_name="", full_data=None, user_info=None, on_submit=None, on_cancel=None):
        self.parent = parent
        self.request_id = request_id
        self.tenant_name = tenant_name
        self.full_data = full_data
        self.user_info = user_info
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        
        try:
            from database.maintaince_service import get_maintenance_staff
            self._staff_list = get_maintenance_staff(user_info=user_info) or []
        except Exception as e:
            self._staff_list = []
            messagebox.showerror("DB Error", f"Could not load staff list:\n{e}")
        
        self._available_slots = []
        self.staff_dropdown = None
        self.date_entry = None
        self.selected_slot = None
        self.comment_text = None
        self._render()

    def _render(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        tk.Label(wrapper, text=f"Assign & Schedule — Request #{self.request_id}", 
                font=("Arial", 12, "bold"), bg="white", anchor="w").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Staff selection
        tk.Label(wrapper, text="Staff Member:", font=("Arial", 10, "bold"), bg="white").grid(row=1, column=0, sticky="w", pady=4)
        self._staff_names = [name for _, name in self._staff_list]
        self._staff_ids = [eid for eid, _ in self._staff_list]
        self.staff_dropdown = ttk.Combobox(wrapper, values=self._staff_names, state="readonly", width=25)
        self.staff_dropdown.grid(row=1, column=1, sticky="w", pady=4)
        self.staff_dropdown.bind('<<ComboboxSelected>>', lambda e: self._check_availability())
        if self._staff_names:
            self.staff_dropdown.current(0)

        # Priority
        tk.Label(wrapper, text="Priority:", font=("Arial", 10, "bold"), bg="white").grid(row=2, column=0, sticky="w", pady=4)
        self.priority_dropdown = ttk.Combobox(wrapper, values=["High", "Medium", "Low"], state="readonly", width=15)
        self.priority_dropdown.set("Medium")
        self.priority_dropdown.grid(row=2, column=1, sticky="w", pady=4)

        # Date
        tk.Label(wrapper, text="Date:", font=("Arial", 10, "bold"), bg="white").grid(row=3, column=0, sticky="w", pady=4)
        self.date_entry = tk.Entry(wrapper, width=15)
        self.date_entry.grid(row=3, column=1, sticky="w", pady=4)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.bind("<KeyRelease>", lambda e: self._check_availability())

        # Available slots display
        tk.Label(wrapper, text="Available Slots:", font=("Arial", 10, "bold"), bg="white").grid(row=4, column=0, sticky="nw", pady=4)
        self.slots_frame = tk.Frame(wrapper, bg="white")
        self.slots_frame.grid(row=4, column=1, columnspan=2, sticky="w", pady=4)

        # Selected slot display
        tk.Label(wrapper, text="Selected Slot:", font=("Arial", 10, "bold"), bg="white").grid(row=5, column=0, sticky="w", pady=4)
        self.slot_label = tk.Label(wrapper, text="None", bg="white", fg="#dc3545", font=("Arial", 10, "bold"))
        self.slot_label.grid(row=5, column=1, sticky="w", pady=4)

        # Comment
        tk.Label(wrapper, text="Comment:", font=("Arial", 10, "bold"), bg="white").grid(row=6, column=0, sticky="nw", pady=4)
        self.comment_text = tk.Text(wrapper, width=40, height=3, font=("Arial", 10))
        self.comment_text.grid(row=6, column=1, columnspan=2, sticky="ew", pady=4)

        wrapper.grid_columnconfigure(1, weight=1)

        # Buttons
        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=(4, 12))
        for text, bg, cmd, w in [
            ("Assign & Schedule", "#3B86FF", self._submit, 180),
            ("Cancel", "#6c757d", self.on_cancel if self.on_cancel else lambda: None, 100),
        ]:
            create_button(btn_frame, text=text, width=w, height=45, bg=bg, fg="white", command=cmd,
                         next_window_func=None, current_window=None).pack(side="left", padx=(0, 8))

        self._check_availability()

    def _check_availability(self, event=None):
        date_str = self.date_entry.get().strip()
        staff_name = self.staff_dropdown.get().strip()
        if not date_str or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str) or not staff_name:
            return

        try:
            from database.maintaince_service import get_staff_task_count_for_date
            task_counts = get_staff_task_count_for_date(staff_name, date_str) or {}

            for widget in self.slots_frame.winfo_children():
                widget.destroy()

            available = []
            for slot in self.TIME_SLOTS:
                count = task_counts.get(slot, 0)
                if count < 1:
                    available.append(slot)

            self._available_slots = available

            if not available:
                tk.Label(self.slots_frame, text="No available slots - all slots booked", 
                        bg="white", fg="#dc3545", font=("Arial", 10)).pack(anchor="w")
                return

            tk.Label(self.slots_frame, text=f"{len(available)} slot(s) available:", 
                    bg="white", fg="#28a745", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 8))
            
            btn_container = tk.Frame(self.slots_frame, bg="white")
            btn_container.pack(anchor="w", fill="x")
            
            for slot in available:
                btn = tk.Button(btn_container, text=self._format_slot_display(slot), bg="#d4edda", fg="#155724", 
                               width=20, height=3, font=("Arial", 10, "bold"), relief="raised",
                               bd=2, cursor="hand2", command=lambda s=slot: self._select_slot(s))
                btn.pack(side="left", padx=8, pady=4, expand=True, fill="x")

            tk.Label(self.slots_frame, text="Click on a time slot above to select it", 
                    bg="white", fg="#6c757d", font=("Arial", 9, "italic")).pack(anchor="w", pady=(8, 0))

        except Exception as e:
            messagebox.showerror("Error", f"Could not check availability:\n{e}")

    def _format_slot_display(self, slot):
        periods = {
            "09:00": "Morning 9:00 AM",
            "13:00": "Afternoon 1:00 PM", 
            "17:00": "Evening 5:00 PM"
        }
        return periods.get(slot, slot)

    def _select_slot(self, slot):
        self.selected_slot = slot
        self.slot_label.config(text=self._format_slot_display(slot), fg="#28a745")

    def _submit(self):
        staff_name = self.staff_dropdown.get().strip()
        priority = self.priority_dropdown.get().strip()
        date_str = self.date_entry.get().strip()
        comment = self.comment_text.get("1.0", "end").strip()

        try:
            validate_staff_assignment(staff_name, priority, date_str, self.selected_slot, comment)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        try:
            employee_id = self._staff_ids[self._staff_names.index(staff_name)]
            scheduled_dt = f"{date_str} {self.selected_slot}:00"
            
            from database.maintaince_service import assign_and_schedule
            result = assign_and_schedule(self.request_id, employee_id, priority, scheduled_dt, comment)
            
            if result and self.on_submit:
                self.on_submit(self.request_id, staff_name, comment)
            else:
                messagebox.showerror("Error", "Operation failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ============================================================================
# MAINTENANCE DETAIL PANEL (HORIZONTAL 3-COLUMN DESIGN)
# ============================================================================

class MaintenanceDetailPanel:
    """Display request details in 3 side-by-side columns"""
    
    INITIAL_FIELDS = ["Request ID", "Date Submitted", "Issue", "Tenant", "Apt Type", "Postcode", "Assigned Date"]
    ASSIGN_FIELDS = ["Description", "Priority", "Staff"]
    RESOLVE_FIELDS = ["Resolved Date", "Status", "Notes"]

    def __init__(self, parent, full_data, on_approve=None, on_deny=None, on_resolve=None):
        self.parent = parent
        self.full_data = list(full_data)
        self.on_approve = on_approve
        self.on_deny = on_deny
        self.on_resolve = on_resolve
        self.priority_update_dropdown = None
        self._render()

    def _render(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        container = tk.Frame(self.parent, bg="#f8f9fa")
        container.pack(fill="both", expand=True, padx=16, pady=12)

        column_frame = tk.Frame(container, bg="#f8f9fa")
        column_frame.pack(fill="both", expand=True)

        # Initial Info
        initial_frame = tk.Frame(column_frame, bg="#ffffff", bd=1, relief="solid")
        initial_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(initial_frame, text="Initial Information", font=("Arial", 12, "bold"), bg="#ffffff").pack(anchor="w", pady=5)
        for i, field in enumerate(self.INITIAL_FIELDS):
            val = self.full_data[i] if i < len(self.full_data) else "—"
            row_frame = tk.Frame(initial_frame, bg="#f1f3f5")
            row_frame.pack(fill="x", pady=2, padx=5)
            tk.Label(row_frame, text=f"{field}:", font=("Arial", 10, "bold"), width=15, anchor="w", bg="#f1f3f5").pack(side="left")
            tk.Label(row_frame, text=val or "—", bg="#f1f3f5").pack(side="left")

        # Assignment Info
        assign_frame = tk.Frame(column_frame, bg="#ffffff", bd=1, relief="solid")
        assign_frame.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(assign_frame, text="Assignment Information", font=("Arial", 12, "bold"), bg="#ffffff").pack(anchor="w", pady=5)
        for i, field in enumerate(self.ASSIGN_FIELDS, start=len(self.INITIAL_FIELDS)):
            val = self.full_data[i] if i < len(self.full_data) else "—"
            row_frame = tk.Frame(assign_frame, bg="#e9ecef")
            row_frame.pack(fill="x", pady=2, padx=5)
            tk.Label(row_frame, text=f"{field}:", font=("Arial", 10, "bold"), width=15, anchor="w", bg="#e9ecef").pack(side="left")
            tk.Label(row_frame, text=val or "—", bg="#e9ecef").pack(side="left")

        # Resolution Info
        resolve_frame = tk.Frame(column_frame, bg="#ffffff", bd=1, relief="solid")
        resolve_frame.pack(side="left", fill="both", expand=True, padx=(5,0))
        tk.Label(resolve_frame, text="Resolution / Status", font=("Arial", 12, "bold"), bg="#ffffff").pack(anchor="w", pady=5)
        for i, field in enumerate(self.RESOLVE_FIELDS, start=len(self.INITIAL_FIELDS)+len(self.ASSIGN_FIELDS)):
            val = self.full_data[i] if i < len(self.full_data) else "—"
            row_frame = tk.Frame(resolve_frame, bg="#f1f3f5")
            row_frame.pack(fill="x", pady=2, padx=5)
            tk.Label(row_frame, text=f"{field}:", font=("Arial", 10, "bold"), width=15, anchor="w", bg="#f1f3f5").pack(side="left")
            tk.Label(row_frame, text=val or "—", bg="#f1f3f5").pack(side="left")

        # Buttons
        status = self.full_data[5] if len(self.full_data) > 5 else ""
        staff = self.full_data[11] if len(self.full_data) > 11 else ""
        assigned_date = self.full_data[12] if len(self.full_data) > 12 else ""

        btn_frame = tk.Frame(container, bg="#f8f9fa")
        btn_frame.pack(anchor="e", pady=10)

        if status == "Open":
            create_button(btn_frame, text="Approve", width=120, height=40, bg="#28a745", fg="white", 
                          command=self.on_approve if self.on_approve else lambda: None,
                          next_window_func=None, current_window=None).pack(side="left", padx=5)
            create_button(btn_frame, text="Deny", width=120, height=40, bg="#dc3545", fg="white",
                          command=self.on_deny if self.on_deny else lambda: None,
                          next_window_func=None, current_window=None).pack(side="left", padx=5)
        
        elif status == "In Progress" and staff and assigned_date:
            mark_btn = create_button(btn_frame, text="Mark Resolved", width=140, height=40, bg="#17a2b8", fg="white",
                          command=self._open_resolve, next_window_func=None, current_window=None)
            mark_btn.pack(side="left", padx=5)

            self.priority_update_dropdown = ttk.Combobox(btn_frame, values=["High", "Medium", "Low"], state="readonly",
                                                         width=10, font=("Arial", 10, "bold"))
            current_priority = self.full_data[2] if len(self.full_data) > 2 else "Medium"
            self.priority_update_dropdown.set(current_priority)
            self.priority_update_dropdown.pack(side="left", padx=5, pady=2, ipadx=5, ipady=6)
            self.priority_update_dropdown.bind("<<ComboboxSelected>>", self._update_priority_immediate)

    def _update_priority_immediate(self, event):
        new_priority = self.priority_update_dropdown.get()
        request_id = self.full_data[0]
        if not new_priority:
            return
        try:
            from database.maintaince_service import update_request_priority
            update_request_priority(request_id, new_priority)
            self.full_data[2] = new_priority
            self._render()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update priority:\n{e}")


    def _open_resolve(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.parent, bg="#f8f9fa", bd=1, relief="solid")
        frame.pack(fill="x", padx=16, pady=10)

        tk.Label(frame, text="Resolution Details", font=("Arial", 13, "bold"), bg="#f8f9fa").pack(anchor="w", pady=5)
        current_issue = self.full_data[7] if len(self.full_data) > 7 else ""
        tk.Label(frame, text=f"Issue: {current_issue}", font=("Arial", 10), bg="#f8f9fa", fg="#555").pack(anchor="w", pady=2)
        assigned_date = self.full_data[12] if len(self.full_data) > 12 else ""
        if assigned_date:
            tk.Label(frame, text=f"Assigned Date: {assigned_date}", font=("Arial", 10), bg="#f8f9fa", fg="#555").pack(anchor="w", pady=2)

        tk.Label(frame, text="Resolution Notes:", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w", pady=(10, 0))
        self.resolve_text = tk.Text(frame, height=3, width=50)
        self.resolve_text.pack(fill="x", pady=5)

        tk.Label(frame, text="Repair Time (hours):", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w")
        self.time_entry = tk.Entry(frame, width=15)
        self.time_entry.pack(anchor="w", pady=2)

        tk.Label(frame, text="Repair Cost (£):", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w")
        self.cost_entry = tk.Entry(frame, width=15)
        self.cost_entry.pack(anchor="w", pady=2)

        btn_frame = tk.Frame(frame, bg="#f8f9fa")
        btn_frame.pack(anchor="e", pady=10)

        create_button(btn_frame, text="Submit", width=100, height=35, bg="#28a745", fg="white", 
                      command=self._submit_resolve, next_window_func=None, current_window=None).pack(side="left", padx=5)
        create_button(btn_frame, text="Cancel", width=100, height=35, bg="#6c757d", fg="white",
                      command=self._render, next_window_func=None, current_window=None).pack(side="left", padx=5)


    def _submit_resolve(self):
        notes = self.resolve_text.get("1.0", "end").strip()
        time_str = self.time_entry.get().strip()
        cost_str = self.cost_entry.get().strip()

        try:
            repair_time = int(time_str) if time_str else None
            repair_cost = float(cost_str) if cost_str else None
        except ValueError:
            messagebox.showerror("Error", "Invalid number format for time or cost")
            return

        try:
            validate_resolution_form(notes, time_str, cost_str)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        if self.on_resolve:
            self.on_resolve(notes, repair_time, repair_cost)


# ============================================================================
# PAGE FACTORY
# ============================================================================

def create_page(parent, user_info=None):
    from main.Lifecycle_page import MaintenanceManagementPage
    page = MaintenanceManagementPage(parent, user_info=user_info)
    
    def on_show():
        page.refresh_data()
    
    page.frame.on_show = on_show
    return page.frame