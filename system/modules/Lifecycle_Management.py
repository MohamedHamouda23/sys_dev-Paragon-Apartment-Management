# ============================================================================
# LIFECYCLE MANAGEMENT MODULE
# Handles staff assignment, scheduling, and request resolution
# ============================================================================

import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from main.helpers import create_button
from validations import validate_staff_assignment, validate_resolution_form


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
        
        # Load staff list
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
        """Render the panel UI"""
        for widget in self.parent.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=16, pady=12)

        # Header
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

        if self.tenant_name:
            self.comment_text.insert("1.0", f"Dear {self.tenant_name},\nMaintenance scheduled for request #{self.request_id}.")

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
        """Check staff availability and show available slots"""
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
                tk.Label(self.slots_frame, text="No available slots - all slots booked for this date", 
                        bg="white", fg="#dc3545", font=("Arial", 10)).pack(anchor="w")
                if len(task_counts) >= 3:
                    tk.Label(self.slots_frame, text="(Staff has reached maximum 3 tasks for this day)", 
                            bg="white", fg="#dc3545", font=("Arial", 9, "italic")).pack(anchor="w")
                return

            tk.Label(self.slots_frame, text=f"{len(available)} slot(s) available:", 
                    bg="white", fg="#28a745", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 8))
            
            btn_container = tk.Frame(self.slots_frame, bg="white")
            btn_container.pack(anchor="w", fill="x")
            
            for i, slot in enumerate(available):
                slot_display = self._format_slot_display(slot)
                btn = tk.Button(btn_container, text=slot_display, bg="#d4edda", fg="#155724", 
                               width=20, height=3, font=("Arial", 10, "bold"), relief="raised",
                               bd=2, cursor="hand2", command=lambda s=slot: self._select_slot(s))
                btn.pack(side="left", padx=8, pady=4, expand=True, fill="x")

            tk.Label(self.slots_frame, text="Click on a time slot above to select it", 
                    bg="white", fg="#6c757d", font=("Arial", 9, "italic")).pack(anchor="w", pady=(8, 0))

        except Exception as e:
            messagebox.showerror("Error", f"Could not check availability:\n{e}")

    def _format_slot_display(self, slot):
        """Format slot for display"""
        periods = {
            "09:00": "Morning\n9:00 AM",
            "13:00": "Afternoon\n1:00 PM", 
            "17:00": "Evening\n5:00 PM"
        }
        return periods.get(slot, slot)

    def _select_slot(self, slot):
        """Handle slot selection"""
        self.selected_slot = slot
        self.slot_label.config(text=self._format_slot_display(slot).replace('\n', ' '), fg="#28a745")

    def _submit(self):
        """Submit staff assignment"""
        staff_name = self.staff_dropdown.get().strip()
        priority = self.priority_dropdown.get().strip()
        date_str = self.date_entry.get().strip()
        comment = self.comment_text.get("1.0", "end").strip()

        # Validate using centralized validation
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
# MAINTENANCE DETAIL PANEL
# ============================================================================

class MaintenanceDetailPanel:
    """Display full request details with conditional buttons"""
    
    LABELS = ("Request ID", "Description", "Priority", "Date Submitted", "Resolved Date", 
              "Status", "Notes", "Issue", "Tenant", "Apt Type", "Postcode", "Staff", "Assigned Date")

    def __init__(self, parent, full_data, on_approve=None, on_deny=None, on_resolve=None):
        self.parent = parent
        self.full_data = full_data
        self.on_approve = on_approve
        self.on_deny = on_deny
        self.on_resolve = on_resolve
        self._render()

    def _render(self):
        """Render detail view"""
        for widget in self.parent.winfo_children():
            widget.destroy()

        grid = tk.Frame(self.parent, bg="white")
        grid.pack(fill="x", padx=16, pady=10)

        # Display fields in two columns
        for i, (lbl, val) in enumerate(zip(self.LABELS, self.full_data[:13])):
            row, col = divmod(i, 2)
            tk.Label(grid, text=f"{lbl}:", font=("Arial", 10, "bold"), bg="white").grid(row=row, column=col*2, sticky="w", padx=5, pady=2)
            tk.Label(grid, text=val or "—", bg="white").grid(row=row, column=col*2+1, sticky="w", padx=5, pady=2)

        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(3, weight=1)

        status = self.full_data[5] if len(self.full_data) > 5 else ""
        staff = self.full_data[11] if len(self.full_data) > 11 else ""
        assigned_date = self.full_data[12] if len(self.full_data) > 12 else ""

        btn_frame = tk.Frame(self.parent, bg="white")
        btn_frame.pack(anchor="e", padx=16, pady=10)

        # Show Approve/Deny for Open requests
        if status == "Open":
            create_button(btn_frame, text="Approve", width=120, height=40, bg="#28a745", fg="white", 
                          command=self.on_approve if self.on_approve else lambda: None,
                          next_window_func=None, current_window=None).pack(side="left", padx=5)
            create_button(btn_frame, text="Deny", width=120, height=40, bg="#dc3545", fg="white",
                          command=self.on_deny if self.on_deny else lambda: None,
                          next_window_func=None, current_window=None).pack(side="left", padx=5)
        
        # Show Mark Resolved for In Progress with staff assigned
        elif status == "In Progress" and staff and assigned_date:
            create_button(btn_frame, text="Mark Resolved", width=140, height=40, bg="#17a2b8", fg="white",
                          command=self._open_resolve, next_window_func=None, current_window=None).pack(side="left", padx=5)

    def _open_resolve(self):
        """Show resolution form"""
        for widget in self.parent.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.parent, bg="white")
        frame.pack(fill="x", padx=16, pady=10)

        tk.Label(frame, text="Resolution Details", font=("Arial", 13, "bold"), bg="white").pack(anchor="w", pady=5)

        # Show current issue
        current_issue = self.full_data[7] if len(self.full_data) > 7 else ""
        tk.Label(frame, text=f"Issue: {current_issue}", font=("Arial", 10), bg="white", fg="#555").pack(anchor="w", pady=2)

        # Show assigned date
        assigned_date = self.full_data[12] if len(self.full_data) > 12 else ""
        if assigned_date:
            tk.Label(frame, text=f"Assigned Date: {assigned_date}", font=("Arial", 10), bg="white", fg="#555").pack(anchor="w", pady=2)

        tk.Label(frame, text="Resolution Notes:", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", pady=(10, 0))
        self.resolve_text = tk.Text(frame, height=3, width=50)
        self.resolve_text.pack(fill="x", pady=5)

        tk.Label(frame, text="Repair Time (hours):", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        self.time_entry = tk.Entry(frame, width=15)
        self.time_entry.pack(anchor="w", pady=2)

        tk.Label(frame, text="Repair Cost (£):", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        self.cost_entry = tk.Entry(frame, width=15)
        self.cost_entry.pack(anchor="w", pady=2)

        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(anchor="e", pady=10)

        create_button(btn_frame, text="Submit", width=100, height=35, bg="#28a745", fg="white", 
                      command=self._submit_resolve, next_window_func=None, current_window=None).pack(side="left", padx=5)
        create_button(btn_frame, text="Cancel", width=100, height=35, bg="#6c757d", fg="white",
                      command=self._render, next_window_func=None, current_window=None).pack(side="left", padx=5)

    def _submit_resolve(self):
        """Submit resolution"""
        notes = self.resolve_text.get("1.0", "end").strip()
        time_str = self.time_entry.get().strip()
        cost_str = self.cost_entry.get().strip()

        try:
            repair_time = int(time_str) if time_str else None
            repair_cost = float(cost_str) if cost_str else None
        except ValueError:
            messagebox.showerror("Error", "Invalid number format for time or cost")
            return

        # Validate using centralized validation
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
    """Create lifecycle management page"""
    from main.Lifecycle_page import MaintenanceManagementPage
    page = MaintenanceManagementPage(parent, user_info=user_info)
    
    # Add on_show method to the frame for the main app to call
    def on_show():
        page.refresh_data()
    
    page.frame.on_show = on_show
    return page.frame