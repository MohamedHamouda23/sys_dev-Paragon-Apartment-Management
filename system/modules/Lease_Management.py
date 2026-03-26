# ============================================================================
# LEASE MANAGEMENT MODULE
# Handles lease creation and removal with early termination penalties
# ============================================================================

import tkinter as tk
from tkinter import messagebox
from datetime import date, timedelta

from main.helpers import (
    create_button, clear_frame,
    styled_label, form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE,
)

from database.lease_service import (
    fetch_leases, fetch_tenants,
    create_lease, build_tenant_map,
)
from database.property_service import build_apartment_map, fetch_available_apartments

from validations import validate_lease_selection, validate_lease_details


# ============================================================================
# ADD LEASE STEPPER CLASS
# ============================================================================

class AddLeaseStepper:
    """Three-step wizard for creating lease agreements"""

    def __init__(self, parent, refresh_callback):
        # Store parent and refresh callback
        self.box_frame        = parent
        self.refresh_callback = refresh_callback

        # Load tenants and available apartments
        tenants    = fetch_tenants()
        apartments = fetch_available_apartments()

        # Build lookup dictionaries
        self.tenant_map   = build_tenant_map(tenants)
        self.tenant_names = list(self.tenant_map.keys())

        self.apt_map      = build_apartment_map(apartments)
        self.apt_displays = list(self.apt_map.keys())

        # Start with tenant selection
        self.step_tenant()

    # ========================================================================
    # STEP 1: SELECT TENANT
    # ========================================================================

    def step_tenant(self):
        """First step: Select tenant"""
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        # Step header
        styled_label(container, "Add Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 3 — Select Tenant", fg="#888").pack(pady=(0, 8))

        # Check if tenants exist
        if not self.tenant_names:
            styled_label(container, "No tenants registered yet.", fg="#C62828").pack(pady=10)
            return

        # Tenant dropdown
        tenant_cb = form_dropdown(container, "Tenant", self.tenant_names)

        # Next button
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: self.step_apartment(tenant_cb.get()),
            next_window_func=None,
            current_window=None,
        ).pack()

    # ========================================================================
    # STEP 2: SELECT APARTMENT
    # ========================================================================

    def step_apartment(self, tenant_name):
        """Second step: Select apartment"""
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        # Step header
        styled_label(container, "Add Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 3 — Select Apartment", fg="#888").pack(pady=(0, 8))
        styled_label(container, f"Tenant: {tenant_name}", fg="#555").pack(anchor="w")

        # Check if apartments available
        if not self.apt_displays:
            styled_label(container, "No vacant apartments available.", fg="#C62828").pack(pady=10)
            btn_frame = tk.Frame(container, bg=BG)
            btn_frame.pack(pady=(12, 0))
            create_button(
                btn_frame,
                text="← Back",
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=self.step_tenant,
                next_window_func=None,
                current_window=None,
            ).pack()
            return

        # Apartment dropdown
        apt_cb = form_dropdown(container, "Apartment (Vacant)", self.apt_displays)

        # Next button
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: self.step_details(tenant_name, apt_cb.get()),
            next_window_func=None,
            current_window=None,
        ).pack()

    # ========================================================================
    # STEP 3: LEASE DETAILS
    # ========================================================================

    def step_details(self, tenant_name, apt_display):
        """Third step: Enter lease details"""
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        # Step header
        styled_label(container, "Add Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 3 of 3 — Lease Details", fg="#888").pack(pady=(0, 8))

        # Show selected tenant and apartment
        info = tk.Frame(container, bg="#F5F5F5", padx=12, pady=8)
        info.pack(fill="x", pady=(0, 12))
        styled_label(info, f"{tenant_name}  ·  {apt_display}", fg="#555").pack(anchor="w")

        # Date and rent fields
        start_entry = form_field(container, "Start Date (YYYY-MM-DD)", [0])
        end_entry   = form_field(container, "End Date (YYYY-MM-DD)",   [0])
        rent_entry  = form_field(container, "Monthly Rent (£)",        [0])

        # Pre-fill with default dates
        today = date.today()
        start_entry.insert(0, str(today))
        end_entry.insert(0, str(today.replace(year=today.year + 1)))

        # Submit function
        def submit():
            try:
                # Validate selections
                if not tenant_name or not apt_display:
                    messagebox.showerror("Error", "Please select a tenant and apartment.")
                    return
                
                # Validate details
                validate_lease_details(
                    start_entry.get(),
                    end_entry.get(),
                    rent_entry.get()
                )
                
                # Get IDs from lookup dictionaries
                tenant_id = self.tenant_map[tenant_name]
                apt_id    = self.apt_map[apt_display]
                
                # Create lease in database
                create_lease(
                    apt_id,
                    tenant_id,
                    start_entry.get(),
                    end_entry.get(),
                    rent_entry.get(),
                )
                
                # Show success message
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    "✓  Lease created successfully!",
                    fg="#2E7D32",
                ).pack(expand=True)
                self.box_frame.after(1200, self.refresh_callback)
                
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Create button
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Create Lease ✓",
            width=180,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=submit,
            next_window_func=None,
            current_window=None,
        ).pack()


# ============================================================================
# REMOVE LEASE STEPPER CLASS
# ============================================================================

class RemoveLeaseStepper:
    """Two-step wizard for removing leases with early termination penalty"""

    def __init__(self, parent, refresh_callback):
        # Store parent and refresh callback
        self.box_frame        = parent
        self.refresh_callback = refresh_callback
        self.step_select()

    # ========================================================================
    # STEP 1: SELECT LEASE
    # ========================================================================

    def step_select(self):
        """First step: Select lease to remove"""
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        # Step header
        styled_label(container, "Remove Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 2 — Select Lease", fg="#888").pack(pady=(0, 8))

        # Load leases
        leases = fetch_leases()
        if not leases:
            styled_label(container, "No leases found.", fg="#C62828").pack(pady=10)
            return

        # Build lease lookup map
        self.lease_map = {
            f"[{l[0]}] {l[3]} – {l[4]}": l
            for l in leases
        }
        
        # Lease dropdown
        lease_cb = form_dropdown(container, "Lease", list(self.lease_map.keys()))

        # Next button
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Next →",
            width=150,
            height=50,
            bg="#3B86FF",
            fg="white",
            command=lambda: self.step_confirm(self.lease_map[lease_cb.get()]),
            next_window_func=None,
            current_window=None,
        ).pack()

    # ========================================================================
    # STEP 2: CONFIRM REMOVAL
    # ========================================================================

    def step_confirm(self, lease):
        """Second step: Confirm removal with penalty details"""
        # Extract lease data
        (l_id, _apt_id, _ten_id,
         tenant_name, apt_display,
         start, end, rent, status) = lease

        # Calculate early termination penalty
        is_early = date.fromisoformat(str(end)) > date.today()
        penalty  = round(float(rent) * 0.05, 2) if is_early else 0.00
        vacate   = str(date.today() + timedelta(days=30)) if is_early else str(end)

        clear_frame(self.box_frame)
        container = card(self.box_frame)

        # Step header
        styled_label(container, "Remove Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 2 — Confirm", fg="#888").pack(pady=(0, 8))

        # Lease details display
        info = tk.Frame(container, bg="#F5F5F5", padx=14, pady=12)
        info.pack(fill="x", pady=(0, 12))
        for label, value in [
            ("Tenant",       tenant_name),
            ("Apartment",    apt_display),
            ("Lease End",    str(end)),
            ("Vacate By",    vacate),
            ("Monthly Rent", f"£{float(rent):,.2f}"),
            ("Penalty (5%)", f"£{penalty:,.2f}" if is_early else "None"),
        ]:
            row = tk.Frame(info, bg="#F5F5F5")
            row.pack(fill="x", pady=2)
            styled_label(row, f"{label}:", fg="#555").pack(side="left", padx=(0, 8))
            styled_label(row, value,        fg="#222").pack(side="left")

        # Early termination warning
        if is_early:
            styled_label(
                container,
                "⚠  Early termination — 1 month notice + 5% penalty applies.",
                fg="#C62828",
            ).pack(pady=(0, 8))

        # Confirm function
        def confirm():
            try:
                from database.lease_service import update_lease_early_termination
                if is_early:
                    update_lease_early_termination(l_id, penalty)
                else:
                    update_lease_early_termination(l_id, 0)
                    
                # Show success message
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    f"✓  Lease removed.  {'Penalty: £' + str(penalty) if is_early else ''}",
                    fg="#2E7D32",
                ).pack(expand=True)
                self.box_frame.after(1500, self.refresh_callback)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # Action buttons
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(4, 0))
        create_button(
            btn_frame,
            text="Confirm",
            width=150,
            height=50,
            bg="#FF3B3B",
            fg="white",
            command=confirm,
            next_window_func=None,
            current_window=None,
        ).pack(side="left", padx=8)
        create_button(
            btn_frame,
            text="Cancel",
            width=100,
            height=50,
            bg="#888",
            fg="white",
            command=self.step_select,
            next_window_func=None,
            current_window=None,
        ).pack(side="left", padx=8)


# ============================================================================
# PAGE FACTORY
# ============================================================================

def create_page(parent):
    """Create and return lease management page"""
    from main.lease_page import LeaseManagerPage
    return LeaseManagerPage(parent).frame