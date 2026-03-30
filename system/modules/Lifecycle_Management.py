# ============================================================================
# LIFECYCLE MANAGEMENT MODULE
# Handles staff assignment, scheduling, and request resolution
# ============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from main.helpers import (
    create_button, styled_label, styled_entry, form_field, form_dropdown,
    clear_frame, show_placeholder, create_scrollable_treeview, BG, APP_BG
)
from validations import validate_staff_assignment, validate_resolution_form


# ============================================================================
# STAFF ASSIGNMENT PANEL
# ============================================================================

class StaffAssignmentPanel:
    """Staff assignment with 3 fixed time slots per day"""
    
    TIME_SLOTS = ["09:00", "13:00", "17:00"]
    
    def __init__(self, parent, request_id, tenant_name="", user_info=None, on_submit=None, on_cancel=None):
        self.parent = parent
        self.request_id = request_id
        self.tenant_name = tenant_name
        self.user_info = user_info
        self.user_role = user_info[4] if user_info and len(user_info) > 4 else None
        self.is_tenant = self.user_role == "Tenant"
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        self.assignment_completed = False
        
        # Load maintenance staff from database
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
        self.priority_dropdown = None
        self.assign_button = None
        self._render()

    def _render(self):
        """Build the staff assignment form"""
        clear_frame(self.parent)

        main_frame = tk.Frame(self.parent, bg="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Header
        title = (
            f"Set Availability for Request #{self.request_id}"
            if self.is_tenant
            else f"Assign Staff to Request #{self.request_id}"
        )
        styled_label(main_frame, title, font=("Arial", 14, "bold"), fg="#2c3e50").pack(anchor="w")
        
        if self.tenant_name:
            styled_label(main_frame, f"Tenant: {self.tenant_name}", 
                        font=("Arial", 11), fg="#34495e").pack(anchor="w", pady=(5, 0))

        form_frame = tk.Frame(main_frame, bg="#f8f9fa", bd=1, relief="solid")
        form_frame.pack(fill="x", pady=10)

        if self.is_tenant:
            info_row = tk.Frame(form_frame, bg="#f8f9fa")
            info_row.pack(fill="x", pady=8, padx=15)
            styled_label(info_row, "Staff Member:", font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
            styled_label(
                info_row,
                "Assigned automatically based on slot availability",
                font=("Arial", 10),
                fg="#34495e",
            ).pack(side="left", padx=(5, 0))

            priority_row = tk.Frame(form_frame, bg="#f8f9fa")
            priority_row.pack(fill="x", pady=8, padx=15)
            styled_label(priority_row, "Priority:", font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
            styled_label(
                priority_row,
                "Set by maintenance team",
                font=("Arial", 10),
                fg="#34495e",
            ).pack(side="left", padx=(5, 0))
        else:
            # Staff selection dropdown
            staff_row = tk.Frame(form_frame, bg="#f8f9fa")
            staff_row.pack(fill="x", pady=8, padx=15)

            styled_label(staff_row, "Staff Member:", font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")

            if not self._staff_list:
                styled_label(staff_row, "No staff available", font=("Arial", 10), fg="#e74c3c").pack(side="left", padx=(5, 0))
                return

            self._staff_names = [name for _, name in self._staff_list]
            self._staff_ids = [eid for eid, _ in self._staff_list]
            self.staff_dropdown = ttk.Combobox(staff_row, values=self._staff_names, state="readonly", width=30)
            self.staff_dropdown.pack(side="left", padx=(5, 0))
            self.staff_dropdown.bind('<<ComboboxSelected>>', lambda e: self._check_availability())
            if self._staff_names:
                self.staff_dropdown.current(0)

            # Priority dropdown
            priority_row = tk.Frame(form_frame, bg="#f8f9fa")
            priority_row.pack(fill="x", pady=8, padx=15)

            styled_label(priority_row, "Priority:", font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")

            self.priority_dropdown = ttk.Combobox(priority_row, values=["High", "Medium", "Low"], state="readonly", width=15)
            self.priority_dropdown.set("Medium")
            self.priority_dropdown.pack(side="left", padx=(5, 0))

        # Date entry field
        date_row = tk.Frame(form_frame, bg="#f8f9fa")
        date_row.pack(fill="x", pady=8, padx=15)
        
        styled_label(date_row, "Date:", font=("Arial", 10, "bold"), 
                    fg="#2c3e50").pack(side="left")
        
        self.date_entry = tk.Entry(date_row, width=20, font=("Arial", 10))
        self.date_entry.pack(side="left", padx=(5, 0))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.bind("<KeyRelease>", lambda e: self._check_availability())
        self.date_entry.bind("<FocusOut>", lambda e: self._check_availability())

        # Available time slots section
        slots_section = tk.Frame(form_frame, bg="#f8f9fa")
        slots_section.pack(fill="x", pady=8, padx=15)
        
        styled_label(slots_section, "Available Slots:", font=("Arial", 10, "bold"), 
                    fg="#2c3e50").pack(side="left")
        
        self.slots_frame = tk.Frame(slots_section, bg="#f8f9fa")
        self.slots_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Selected slot display
        selected_row = tk.Frame(form_frame, bg="#f8f9fa")
        selected_row.pack(fill="x", pady=8, padx=15)
        
        styled_label(selected_row, "Selected Slot:", font=("Arial", 10, "bold"), 
                    fg="#2c3e50").pack(side="left")
        
        self.slot_label = styled_label(selected_row, "None", font=("Arial", 10, "bold"), fg="#e74c3c")
        self.slot_label.pack(side="left", padx=(5, 0))

        # Assignment description text area
        desc_row = tk.Frame(form_frame, bg="#f8f9fa")
        desc_row.pack(fill="x", pady=8, padx=15)
        
        desc_label = "Request Description:" if self.is_tenant else "Assignment Description:"
        styled_label(desc_row, desc_label, font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left", anchor="n")
        
        self.comment_text = tk.Text(desc_row, width=50, height=4, font=("Arial", 10), 
                                   bd=1, relief="solid")
        self.comment_text.pack(side="left", padx=(5, 0), fill="x", expand=True)

        # Action buttons
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(anchor="e", pady=(15, 0))

        # Cancel button
        create_button(btn_frame, text="Cancel",
                 width=170, height=45,
                 bg="#95a5a6", fg="white",
                     command=self.on_cancel if self.on_cancel else lambda: None).pack(side="left", padx=(0, 10))

        # Assign button
        action_text = "Submit Availability" if self.is_tenant else "Assign & Schedule"
        self.assign_button = create_button(btn_frame, text=action_text,
                          width=230, height=45,
                          bg="#3498db", fg="white",
                                          command=self._submit)
        self.assign_button.pack(side="left")

        # Check availability on load
        self._check_availability()

    def _check_availability(self, event=None):
        """Check staff availability for selected date and display available slots"""
        date_str = self.date_entry.get().strip()
        staff_name = self.staff_dropdown.get().strip() if self.staff_dropdown else ""
        
        if not date_str:
            return

        if not self.is_tenant and not staff_name:
            return
            
        # Validate date format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return

        clear_frame(self.slots_frame)

        try:
            available = []
            if self.is_tenant:
                from database.maintaince_service import get_available_staff_for_slot
                for slot in self.TIME_SLOTS:
                    slot_staff = get_available_staff_for_slot(date_str, slot, user_info=self.user_info) or []
                    if slot_staff:
                        available.append(slot)
            else:
                # Get task counts for each time slot for selected staff member
                from database.maintaince_service import get_staff_task_count_for_date
                task_counts = get_staff_task_count_for_date(staff_name, date_str) or {}
                for slot in self.TIME_SLOTS:
                    count = task_counts.get(slot, 0)
                    if count < 1:
                        available.append(slot)

            self._available_slots = available

            # Display message if no slots available
            if not available:
                styled_label(self.slots_frame, "No slots available for this date", 
                           font=("Arial", 10), fg="#e74c3c").pack(anchor="w")
                return

            # Create slot buttons
            for slot in available:
                slot_btn = create_button(
                self.slots_frame,
                text=self._format_slot_display(slot),
                width=160,
                height=30,
                bg="#2ecc71" if slot == self.selected_slot else "#ecf0f1",
                fg="white" if slot == self.selected_slot else "#2c3e50",
                command=lambda s=slot: self._select_slot(s)
            )

                slot_btn.pack_forget()
                slot_btn.pack(side="left", padx=(0, 10))

        except Exception as e:
            messagebox.showerror("Error", f"Could not check availability:\n{e}")

    def _format_slot_display(self, slot):
        """Format 24-hour time to 12-hour AM/PM format"""
        periods = {"09:00": "9:00 AM", "13:00": "1:00 PM", "17:00": "5:00 PM"}
        return periods.get(slot, slot)

    def _select_slot(self, slot):
        """Handle time slot selection"""
        self.selected_slot = slot
        self.slot_label.config(text=self._format_slot_display(slot), fg="#27ae60")
        self._check_availability()

    def _submit(self):
        """Submit staff assignment"""
        # Prevent double submission
        if self.assignment_completed:
            messagebox.showwarning(
                "Already Assigned",
                "Staff has already been assigned to this request.",
                parent=self.parent,
            )
            return
            
        staff_name = self.staff_dropdown.get().strip() if self.staff_dropdown else ""
        priority = self.priority_dropdown.get().strip() if self.priority_dropdown else "Medium"
        date_str = self.date_entry.get().strip()
        comment = self.comment_text.get("1.0", "end").strip()

        # Validate form inputs
        try:
            validate_staff_assignment(
                staff_name,
                priority,
                date_str,
                self.selected_slot,
                comment,
                require_staff=not self.is_tenant,
                require_priority=not self.is_tenant,
            )
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self.parent)
            return

        # Save assignment to database
        try:
            if self.is_tenant:
                from database.maintaince_service import pick_random_available_staff_for_slot
                chosen = pick_random_available_staff_for_slot(date_str, self.selected_slot, user_info=self.user_info)
                if not chosen:
                    messagebox.showerror(
                        "No Staff Available",
                        "No maintenance staff is available for the selected date and time.",
                        parent=self.parent,
                    )
                    return
                employee_id, staff_name = chosen
                priority = "Medium"
            else:
                employee_id = self._staff_ids[self._staff_names.index(staff_name)]

            scheduled_dt = f"{date_str} {self.selected_slot}:00"
            
            from database.maintaince_service import assign_and_schedule
            result = assign_and_schedule(self.request_id, employee_id, priority, scheduled_dt, comment)
            
            if result:
                self.assignment_completed = True
                self.assign_button.config(state="disabled", bg="#95a5a6")

                if self.on_submit:
                    self.on_submit(self.request_id, staff_name, comment)
                else:
                    messagebox.showinfo(
                        "Success",
                        f"Staff assigned successfully to Request #{self.request_id}",
                        parent=self.parent,
                    )
            else:
                messagebox.showerror("Error", "Failed to assign staff", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.parent)


# ============================================================================
# MAINTENANCE DETAIL PANEL
# ============================================================================

class MaintenanceDetailPanel:
    """Display request details in organized sections"""
    
    # Map field names to data tuple indices
    FIELD_INDICES = {
        'request_id': 0, 'description': 1, 'priority': 2, 'created_date': 3,
        'resolved_date': 4, 'status': 5, 'notes': 6, 'issue': 7,
        'tenant_name': 8, 'apartment_type': 9, 'postcode': 10,
        'staff_name': 11, 'assigned_date': 12, 'is_current': 13,
        'repair_cost': 14, 'repair_time': 15
    }
    
    def __init__(self, parent, full_data, on_approve=None, on_deny=None, 
                 on_resolve=None, on_assign=None, on_update_priority=None, user_info=None):
        self.parent = parent
        self.full_data = list(full_data) if full_data else []
        self.on_approve = on_approve
        self.on_deny = on_deny
        self.on_resolve = on_resolve
        self.on_assign = on_assign
        self.on_update_priority = on_update_priority
        self.user_info = user_info
        self.priority_update_dropdown = None
        self.resolve_notes = None
        self.cost_entry = None
        self.time_entry = None
        self._render()

    def _get_field(self, field_name, default="—"):
        """Get field value from data tuple, return default if not found"""
        idx = self.FIELD_INDICES.get(field_name)
        if idx is not None and idx < len(self.full_data):
            value = self.full_data[idx]
            # Return default if value is None OR empty string
            return value if value not in (None, "") else default
        return default

    def _render(self):
        """Build the request details display"""
        clear_frame(self.parent)

        main_frame = tk.Frame(self.parent, bg="#f0f2f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Header with request ID and status badges
        header_frame = tk.Frame(main_frame, bg="white", bd=1, relief="solid")
        header_frame.pack(fill="x", pady=(0, 15))
        
        request_id = self._get_field('request_id')
        status = self._get_field('status')
        priority = self._get_field('priority')
        
        # Status color mapping
        status_colors = {"Open": "#f39c12", "Approved": "#28a745", "In Progress": "#3498db", 
                        "Resolved": "#27ae60", "Denied": "#e74c3c"}
        status_color = status_colors.get(status, "#95a5a6")
        
        # Priority color mapping
        priority_colors = {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#27ae60"}
        priority_color = priority_colors.get(priority, "#95a5a6")

        tk.Label(header_frame, text=f"Maintenance Request #{request_id}", 
                font=("Arial", 18, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", padx=15, pady=(10, 5))
        
        # Status and priority badges
        badge_frame = tk.Frame(header_frame, bg="white")
        badge_frame.pack(anchor="w", padx=15, pady=(0, 10))
        
        tk.Label(badge_frame, text=f"Status: {status}", bg=status_color, fg="white",
                font=("Arial", 10, "bold"), padx=10, pady=2).pack(side="left", padx=(0, 10))
        
        if status in ["Approved", "In Progress"]:
            tk.Label(badge_frame, text=f"Priority: {priority}", bg=priority_color, fg="white",
                    font=("Arial", 10, "bold"), padx=10, pady=2).pack(side="left")

        # Three column layout
        columns_frame = tk.Frame(main_frame, bg="#f0f2f5")
        columns_frame.pack(fill="both", expand=True)

        # Column 1: Request Information
        col1 = tk.Frame(columns_frame, bg="white", bd=1, relief="solid")
        col1.pack(side="left", fill="both", expand=True, padx=(0, 7))
        styled_label(col1, "Request Information", font=("Arial", 13, "bold"), fg="#2c3e50").pack(anchor="w", padx=12, pady=(10, 5))
        
        request_items = [
            ("Date Submitted:", self._get_field('created_date')),
            ("Issue:", self._get_field('issue')),
            ("Tenant Name:", self._get_field('tenant_name')),
            ("Apartment Type:", self._get_field('apartment_type')),
            ("Postcode:", self._get_field('postcode')),
        ]
        for label, value in request_items:
            row = tk.Frame(col1, bg="white")
            row.pack(fill="x", padx=12, pady=3)
            styled_label(row, label, font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
            styled_label(row, value, font=("Arial", 10), fg="#34495e").pack(side="left", padx=(5, 0))

        # Column 2: Assignment Information
        col2 = tk.Frame(columns_frame, bg="white", bd=1, relief="solid")
        col2.pack(side="left", fill="both", expand=True, padx=7)
        styled_label(col2, "Assignment Information", font=("Arial", 13, "bold"), fg="#2c3e50").pack(anchor="w", padx=12, pady=(10, 5))
        
        staff_name = self._get_field('staff_name')
        assignment_items = [
            ("Assigned Staff:", staff_name if staff_name != "—" else "Not Assigned"),
            ("Assigned Date:", self._get_field('assigned_date')),
            ("Description:", self._get_field('description')),
        ]
        for label, value in assignment_items:
            row = tk.Frame(col2, bg="white")
            row.pack(fill="x", padx=12, pady=3)
            styled_label(row, label, font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
            styled_label(row, value, font=("Arial", 10), fg="#34495e").pack(side="left", padx=(5, 0))

        # Column 3: Resolution Information
        col3 = tk.Frame(columns_frame, bg="white", bd=1, relief="solid")
        col3.pack(side="left", fill="both", expand=True, padx=(7, 0))
        styled_label(col3, "Resolution Information", font=("Arial", 13, "bold"), fg="#2c3e50").pack(anchor="w", padx=12, pady=(10, 5))
        
        resolution_items = [
            ("Resolved Date:", self._get_field('resolved_date')),
            ("Repair Cost (£):", self._get_field('repair_cost')),
            ("Repair Time (hrs):", self._get_field('repair_time')),
            ("Notes:", self._get_field('notes')),
        ]
        for label, value in resolution_items:
            row = tk.Frame(col3, bg="white")
            row.pack(fill="x", padx=12, pady=3)
            styled_label(row, label, font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
            styled_label(row, value, font=("Arial", 10), fg="#34495e").pack(side="left", padx=(5, 0))

        # Action buttons based on status
        self._render_action_buttons(main_frame, status, request_id)

    def _render_action_buttons(self, parent, status, request_id):
        """Render action buttons based on request status"""
        btn_frame = tk.Frame(parent, bg="#f0f2f5")
        btn_frame.pack(anchor="e", pady=(15, 0))

        role = self.user_info[4] if self.user_info and len(self.user_info) > 4 else None
        is_tenant = (role == "Tenant")

        # Open status: show approve/deny for non-tenants only
        if status == "Open":
            if not is_tenant:
                create_button(
                    btn_frame, text="Approve Request", bg="#27ae60", fg="white",
                    command=lambda: self.on_approve(request_id)
                ).pack(side="left", padx=(0, 10))

                create_button(
                    btn_frame, text="Deny Request", bg="#e74c3c", fg="white",
                    command=lambda: self.on_deny(request_id)
                ).pack(side="left")

        # In Progress status: keep same
        elif status == "In Progress":
            if not is_tenant:
                tk.Label(
                    btn_frame, text="Update Priority:", bg="#f0f2f5",
                    font=("Arial", 10, "bold")
                ).pack(side="left", padx=(0, 5))

                current_prio = self._get_field('priority', "Medium")
                self.priority_update_dropdown = ttk.Combobox(
                    btn_frame, values=["High", "Medium", "Low"],
                    state="readonly", width=10
                )
                self.priority_update_dropdown.set(current_prio)
                self.priority_update_dropdown.pack(side="left", padx=(0, 20))

                self.priority_update_dropdown.bind(
                    "<<ComboboxSelected>>",
                    lambda e: self._handle_immediate_priority_update(request_id)
                )

                create_button(
                    btn_frame,
                    text="Mark as Resolved",
                    width=230,
                    height=45,
                    bg="#27ae60",
                    fg="white",
                    command=self._open_resolve_form
                ).pack(side="left")

    def _handle_immediate_priority_update(self, request_id):
        """Handle immediate priority update when dropdown changes"""
        new_prio = self.priority_update_dropdown.get()
        from database.maintaince_service import update_request_priority
        
        if update_request_priority(request_id, new_prio):
            # Trigger refresh in parent page
            if self.on_update_priority:
                self.on_update_priority(request_id)
        else:
            messagebox.showerror("Error", "Failed to update priority.")

    def _open_resolve_form(self):
        """Open resolution form for marking request as resolved"""
        clear_frame(self.parent)
        form_frame = tk.Frame(self.parent, bg="white", bd=1, relief="solid")
        form_frame.pack(fill="both", expand=True, padx=20, pady=15)
        styled_label(form_frame, "Resolve Maintenance Request", font=("Arial", 16, "bold"), fg="#2c3e50").pack(anchor="w", padx=15, pady=(10, 5))
        
        request_id = self._get_field('request_id')
        fields_frame = tk.Frame(form_frame, bg="white")
        fields_frame.pack(fill="x", padx=15, pady=5)

        # Resolution notes text area
        styled_label(fields_frame, "Resolution Notes:", font=("Arial", 10, "bold"), fg="#2c3e50").pack(anchor="w")
        self.resolve_notes = tk.Text(fields_frame, height=4, width=60, font=("Arial", 10), bd=1, relief="solid")
        self.resolve_notes.pack(fill="x", pady=(5, 10))

        # Repair cost entry
        cost_frame = tk.Frame(fields_frame, bg="white")
        cost_frame.pack(fill="x", pady=5)
        styled_label(cost_frame, "Repair Cost (£):", font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
        self.cost_entry = tk.Entry(cost_frame, width=20, font=("Arial", 10))
        self.cost_entry.pack(side="left", padx=(5, 0))

        # Repair time entry
        time_frame = tk.Frame(fields_frame, bg="white")
        time_frame.pack(fill="x", pady=5)
        styled_label(time_frame, "Repair Time (hours):", font=("Arial", 10, "bold"), fg="#2c3e50").pack(side="left")
        self.time_entry = tk.Entry(time_frame, width=20, font=("Arial", 10))
        self.time_entry.pack(side="left", padx=(5, 0))

        # Action buttons
        btn_frame = tk.Frame(form_frame, bg="white")
        btn_frame.pack(anchor="e", padx=15, pady=(15, 10))
        create_button(
            btn_frame,
            text="Cancel",
            width=170,
            height=45,
            bg="#95a5a6",
            fg="white",
            command=lambda: self._render()
        ).pack(side="left", padx=(0, 10))
        create_button(
            btn_frame,
            text="Submit Resolution",
            width=230,
            height=45,
            bg="#27ae60",
            fg="white",
            command=self._submit_resolution
        ).pack(side="left")

    def _submit_resolution(self):
        """Submit resolution form"""
        notes = self.resolve_notes.get("1.0", "end").strip()
        cost_str = self.cost_entry.get().strip()
        time_str = self.time_entry.get().strip()
        
        # Validate resolution form
        try:
            validate_resolution_form(notes, time_str, cost_str)
            repair_cost = float(cost_str) if cost_str else 0
            repair_time = float(time_str) if time_str else 0
            if self.on_resolve:
                self.on_resolve(notes, repair_cost, repair_time)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self.parent)


def create_page(parent, user_info):
    """Factory function to create lifecycle management page"""
    from main.Lifecycle_page import MaintenanceManagementPage
    page = MaintenanceManagementPage(parent, user_info=user_info)
    def on_show():
        page.refresh_data()
    page.frame.on_show = on_show
    return page.frame
