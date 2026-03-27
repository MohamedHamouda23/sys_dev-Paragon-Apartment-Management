# ============================================================================
# LEASE MANAGEMENT MODULE
# Handles lease creation and removal with early termination penalties
# ============================================================================

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import date, timedelta

try:
    from tkcalendar import DateEntry
    HAS_DATE_ENTRY = True
except Exception:
    HAS_DATE_ENTRY = False
    DateEntry = None


def _resolve_date_entry():
    """Resolve DateEntry lazily so it can work after package installation."""
    global HAS_DATE_ENTRY, DateEntry
    if HAS_DATE_ENTRY and DateEntry is not None:
        return DateEntry
    try:
        from tkcalendar import DateEntry as _DateEntry
        HAS_DATE_ENTRY = True
        DateEntry = _DateEntry
        return DateEntry
    except Exception:
        HAS_DATE_ENTRY = False
        DateEntry = None
        return None

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
from database.tenant_portal_service import (
    get_tenant_profile,
    submit_early_termination_request,
)

from validations import validate_lease_selection, validate_lease_details


# ============================================================================
# ADD LEASE STEPPER CLASS
# ============================================================================
class AddLeaseStepper:
    def __init__(self, parent, refresh_callback, city_id=None): 
        self.box_frame        = parent
        self.refresh_callback = refresh_callback
        self.city_id          = city_id 

        # FIX: Pass city_id to both fetch functions
        tenants    = fetch_tenants(city_id=self.city_id)
        apartments = fetch_available_apartments(city_id=self.city_id)

        # Rest of the code remains the same...
        self.tenant_map   = {t[1]: t[0] for t in tenants} # name: id
        self.tenant_names = list(self.tenant_map.keys())
        self.apt_map      = build_apartment_map(apartments)
        self.apt_displays = list(self.apt_map.keys())

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
                validate_lease_selection(tenant_name, apt_display)
                
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

class TenantLeaseExitPage:
    def __init__(self, parent, user_info):
        self.user_info = user_info
        self.user_id = user_info[0] if user_info else None
        self.frame = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self._load_data()

    def _build_layout(self):
        wrap = tk.Frame(self.frame, bg="#c9e4c4")
        wrap.pack(fill="both", expand=True, padx=20, pady=20)

        # Keep cards full-width while centering the whole section vertically.
        top_spacer = tk.Frame(wrap, bg="#c9e4c4")
        top_spacer.pack(fill="both", expand=True)

        content = tk.Frame(wrap, bg="#c9e4c4")
        content.pack(fill="x")

        info = tk.Frame(content, bg="white", bd=2, relief="groove")
        info.pack(fill="x", pady=(0, 10))
        tk.Label(info, text="Lease", bg="white", fg="#1f3b63", font=("Arial", 15, "bold")).pack(
            anchor="w", padx=12, pady=(10, 8)
        )

        self.lease_labels = {}
        for key in ["Tenant", "Location", "Type", "Monthly Rent", "Lease End"]:
            row = tk.Frame(info, bg="white")
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=f"{key}:", bg="white", fg="#4c5d73", width=14, anchor="w", font=("Arial", 10, "bold")).pack(side="left")
            lbl = tk.Label(row, text="-", bg="white", fg="#1f3b63", font=("Arial", 10))
            lbl.pack(side="left")
            self.lease_labels[key] = lbl

        form = tk.Frame(content, bg="white", bd=2, relief="groove")
        form.pack(fill="x", pady=(0, 0))
        tk.Label(form, text="Request Early Termination", bg="white", fg="#1f3b63", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 8)
        )
        tk.Label(form, text="Move-out Date", bg="white", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky="w", padx=10, pady=4
        )
        date_entry_cls = _resolve_date_entry()
        if date_entry_cls is not None:
            self.move_out_entry = date_entry_cls(
                form,
                width=16,
                date_pattern="yyyy-mm-dd",
                mindate=date.today(),
            )
        else:
            self.move_out_entry = tk.Entry(form, width=20)
            self.move_out_entry.insert(0, "YYYY-MM-DD")
        self.move_out_entry.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        tk.Label(form, text="Move-out Time", bg="white", font=("Arial", 10, "bold")).grid(
            row=1, column=2, sticky="w", padx=10, pady=4
        )
        self.move_out_time = ttk.Combobox(
            form,
            values=["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
            state="readonly",
            width=12,
        )
        self.move_out_time.grid(row=1, column=3, sticky="w", padx=6, pady=4)
        self.move_out_time.set("10:00")

        tk.Button(
            form,
            text="Submit Request",
            command=self._submit,
            bg="#dc3545",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=12,
            pady=6,
        ).grid(row=3, column=1, sticky="e", padx=10, pady=8)

        tk.Label(
            form,
            text="Rule: 1 month notice required. Penalty is 5% of monthly rent.",
            bg="white",
            fg="#8a3b37",
            font=("Arial", 9, "italic"),
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=10)

        bottom_spacer = tk.Frame(wrap, bg="#c9e4c4")
        bottom_spacer.pack(fill="both", expand=True)

    def on_show(self):
        self._load_data()

    def _load_data(self):
        profile = get_tenant_profile(self.user_id)
        if profile:
            self.lease_labels["Tenant"].config(text=profile.get("name", "-"))
            self.lease_labels["Location"].config(text=profile.get("location", "-"))
            self.lease_labels["Type"].config(text=profile.get("apartment_type", "-"))
            self.lease_labels["Monthly Rent"].config(text=f"GBP {float(profile.get('monthly_rent', 0)):.2f}")
            self.lease_labels["Lease End"].config(text=profile.get("lease_end") or "N/A")

    def _submit(self):
        date_entry_cls = _resolve_date_entry()
        if date_entry_cls is not None and isinstance(self.move_out_entry, date_entry_cls):
            move_out = self.move_out_entry.get_date().strftime("%Y-%m-%d")
        else:
            move_out = self.move_out_entry.get().strip()
        if not move_out:
            messagebox.showerror("Validation Error", "Move-out date is required.")
            return
        try:
            move_out_dt = date.fromisoformat(move_out)
        except Exception:
            messagebox.showerror("Validation Error", "Move-out date must be in YYYY-MM-DD format.")
            return

        if move_out_dt < date.today():
            messagebox.showerror("Validation Error", "Move-out date cannot be before today.")
            return
        try:
            penalty = submit_early_termination_request(self.user_id, move_out, "")
            messagebox.showinfo("Submitted", f"Request submitted. Penalty: GBP {penalty:.2f}")
            self._load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

def create_page(parent, user_info):
    """Create and return lease management page"""
    # 1. Check if user_info exists and has the expected length
    if not user_info or len(user_info) < 5:
        from main.lease_page import LeaseManagerPage
        return LeaseManagerPage(parent, user_info=None).frame
    role = user_info[4] 
    if role == "Tenant":
        page = TenantLeaseExitPage(parent, user_info=user_info)
        page.frame.on_show = page.on_show
        return page.frame
    
    # For Administrators/Staff
    from main.lease_page import LeaseManagerPage
    return LeaseManagerPage(parent, user_info=user_info).frame