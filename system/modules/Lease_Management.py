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
    update_lease_early_termination,
)
from database.property_service import build_apartment_map, fetch_available_apartments
from database.tenant_portal_service import (
    get_tenant_profile,
    get_active_lease_for_user,
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
                    apartment_id=apt_id,
                    tenant_id=tenant_id,
                    start_date=start_entry.get(),
                    end_date=end_entry.get(),
                    agreed_rent=rent_entry.get()
                )
                
                # Show success message
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    "✓  Lease created successfully",
                    fg="#2E7D32",
                ).pack(expand=True)
                
                # Refresh and return to main view after 1.5 seconds
                self.box_frame.after(1500, self.refresh_callback)
                
            except Exception as err:
                messagebox.showerror("Error", str(err))

        # Action buttons
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=(20, 0))
        create_button(
            btn_frame,
            text="Create Lease",
            width=150,
            height=50,
            bg="#2E7D32",
            fg="white",
            command=submit,
            next_window_func=None,
            current_window=None,
        ).pack()


# ============================================================================
# REMOVE LEASE STEPPER CLASS
# ============================================================================
class RemoveLeaseStepper:
    def __init__(self, parent, refresh_callback):
        self.box_frame        = parent
        self.refresh_callback = refresh_callback
        self.leases           = fetch_leases()
        
        self.step_select()

    def step_select(self):
        """First step: Select a lease to remove"""
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        # Header
        styled_label(container, "Remove Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 2 — Select Lease", fg="#888").pack(pady=(0, 8))

        # Check if leases exist
        if not self.leases:
            styled_label(container, "No active leases found.", fg="#C62828").pack(pady=10)
            return

        # Display leases in dropdown format
        lease_options = []
        for lease in self.leases:
            l_id, tenant, apt, start, end, rent, city, status = lease
            lease_str = f"#{l_id} - {tenant} ({apt}) - {status}"
            lease_options.append(lease_str)

        lease_cb = form_dropdown(container, "Select Lease", lease_options)

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
            command=lambda: self.step_confirm(lease_cb.get()),
            next_window_func=None,
            current_window=None,
        ).pack()

    def step_confirm(self, lease_str):
        """Second step: Confirm removal with penalty calculation"""
        if not lease_str:
            messagebox.showerror("Error", "Please select a lease.")
            return

        # Extract lease ID from string (format: "#ID - ...")
        l_id = int(lease_str.split("#")[1].split(" ")[0])
        
        # Find the corresponding lease
        lease_data = next((l for l in self.leases if l[0] == l_id), None)
        if not lease_data:
            messagebox.showerror("Error", "Lease not found.")
            return

        l_id, tenant, apt, start, end_str, rent_str, city, status = lease_data
        
        # Parse dates
        end_date = date.fromisoformat(str(end_str))
        today = date.today()
        
        # Calculate penalty
        is_early = end_date > today
        rent = float(rent_str.replace("£", "").replace(",", ""))
        penalty = round(rent * 0.05, 2) if is_early else 0.0
        vacate_date = str(today + timedelta(days=30)) if is_early else end_str

        # Display confirmation
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        styled_label(container, "Remove Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 2 — Confirm Removal", fg="#888").pack(pady=(0, 8))

        # Lease details
        info = tk.Frame(container, bg="#F5F5F5", padx=12, pady=8)
        info.pack(fill="x", pady=(0, 12))
        styled_label(info, f"Tenant: {tenant}", fg="#555").pack(anchor="w", pady=2)
        styled_label(info, f"Apartment: {apt}", fg="#555").pack(anchor="w", pady=2)
        styled_label(info, f"End Date: {end_str}", fg="#555").pack(anchor="w", pady=2)
        styled_label(info, f"Vacate By: {vacate_date}", fg="#555").pack(anchor="w", pady=2)
        
        if is_early:
            styled_label(info, f"Early Termination Penalty (5%): £{penalty:,.2f}", fg="#C62828").pack(anchor="w", pady=2)
            styled_label(
                container,
                "⚠  Early termination — 1 month notice + 5% penalty applies.",
                fg="#C62828",
            ).pack(pady=(0, 8))

        # Confirm function
        def confirm():
            try:
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
        # Header
        header = tk.Frame(self.frame, bg="#c9e4c4")
        header.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(header, text="My Leases", bg="#c9e4c4", fg="#1f3b63", font=("Arial", 18, "bold")).pack(side="left")

        # Scrollable Container Setup
        container = tk.Frame(self.frame, bg="#c9e4c4")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(container, bg="#c9e4c4", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#c9e4c4")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # Ensure the scroll frame matches canvas width
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_show(self):
        self._load_data()

    def _load_data(self):
        """Load all leases for the current tenant from database"""
        # Clear existing lease cards
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Get the actual tenant_id for this user
        from database.tenant_portal_service import get_tenant_id_from_user
        tenant_id = get_tenant_id_from_user(self.user_id)
        
        if not tenant_id:
            tk.Label(self.scroll_frame, text="No tenant profile found.", 
                    bg="#c9e4c4", font=("Arial", 12)).pack(pady=20)
            return

    # Direct database query to get all leases for this tenant
        from database.databaseConnection import check_connection
        conn = check_connection()
        cursor = conn.cursor()
        
        # Query that returns all leases with complete details
        cursor.execute("""
        SELECT 
            l.lease_id,
            u.first_name || ' ' || u.surname as tenant_name,
            a.type || ' - ' || b.street || ', ' || b.postcode as apt_display,
            l.start_date,
            l.end_date,
            l.Agreed_rent,
            loc.city_name,
            CASE 
                WHEN l.early_termination_fee > 0 THEN 'Terminated'
                WHEN DATE(l.end_date) >= DATE('now') THEN 'Active'
                ELSE 'Expired'
            END as status,
            l.tenant_id,
            l.deposit,
            l.early_termination_fee
        FROM Lease l
        JOIN Tenant t ON l.tenant_id = t.tenant_id
        JOIN User u ON t.user_id = u.user_id
        JOIN Apartments a ON l.apartment_id = a.apartment_id
        JOIN Buildings b ON a.building_id = b.building_id
        JOIN Location loc ON b.city_id = loc.city_id
        WHERE t.tenant_id = ?
        AND u.city_id = ?
        AND b.city_id = ?
        ORDER BY 
            CASE 
                WHEN l.early_termination_fee > 0 THEN 2
                WHEN DATE(l.end_date) >= DATE('now') THEN 0
                ELSE 1
            END,
            l.end_date DESC
    """, (tenant_id, self.user_info[5], self.user_info[5]))
        
        tenant_leases = cursor.fetchall()
        conn.close()
        
        if not tenant_leases:
            tk.Label(self.scroll_frame, text="No lease records found.", 
                    bg="#c9e4c4", font=("Arial", 12)).pack(pady=20)
            return

        # Display each lease
        for lease in tenant_leases:
            self._create_lease_card(lease)

    def _create_lease_card(self, lease):
        """Create a card for a single lease"""
        # lease format: (id, tenant_name, apt_display, start, end, rent, city, status, tenant_id, deposit, early_fee)
        l_id, tenant_name, apt_display, start, end, rent, city, status, tenant_id, deposit, early_fee = lease
        
        # Determine UI colors based on status
        is_active = (status == "Active")
        card_bg = "white"
        status_color = "#2E7D32" if is_active else "#C62828"
        
        # Convert rent to float safely
        try:
            rent_amount = float(rent)
        except (TypeError, ValueError):
            rent_amount = 0.0

        # Create card frame
        card = tk.Frame(self.scroll_frame, bg=card_bg, bd=2, relief="groove", padx=15, pady=15)
        card.pack(fill="x", pady=8, padx=5)

        # Left side - Lease details
        info_frame = tk.Frame(card, bg=card_bg)
        info_frame.pack(side="left", fill="both", expand=True)

        # Apartment info
        tk.Label(info_frame, text=f"Apartment: {apt_display}", bg=card_bg, 
                 font=("Arial", 12, "bold"), fg="#1f3b63").pack(anchor="w")
        
        # Location and rent
        tk.Label(info_frame, text=f"Location: {city} | Rent: £{rent_amount:,.2f}/month", 
                 bg=card_bg, font=("Arial", 10)).pack(anchor="w")
        
        # Status with color coding
        tk.Label(info_frame, text=f"STATUS: {status.upper()}", bg=card_bg, 
                 font=("Arial", 10, "bold"), fg=status_color).pack(anchor="w")
        
        # Lease period
        tk.Label(info_frame, text=f"Period: {start} to {end}", bg=card_bg, 
                 font=("Arial", 9), fg="#555").pack(anchor="w")
        
        # Deposit info
        if deposit:
            tk.Label(info_frame, text=f"Deposit: £{float(deposit):,.2f}", bg=card_bg, 
                     font=("Arial", 9), fg="#555").pack(anchor="w")

        # Right side - Action buttons
        if is_active:
            btn_frame = tk.Frame(card, bg=card_bg)
            btn_frame.pack(side="right", padx=10)
            
            # Termination button
            tk.Button(
                btn_frame,
                text="Terminate Lease",
                bg="#dc3545",
                fg="white",
                font=("Arial", 9, "bold"),
                command=lambda lid=l_id, r=rent_amount: self._terminate_lease(lid, r),
                relief="flat",
                padx=10,
                pady=5
            ).pack()
            
            # Info about penalty
            tk.Label(btn_frame, text=f"Penalty: 5% (£{rent_amount * 0.05:,.2f})", 
                     bg=card_bg, font=("Arial", 8), fg="#dc3545").pack(pady=(5, 0))
        else:
            # Show "PAST LEASE" label for expired/terminated leases
            tk.Label(card, text="PAST LEASE", font=("Arial", 10, "bold"), 
                     fg="#888", bg=card_bg).pack(side="right", padx=20)

    def _terminate_lease(self, lease_id, rent):
        """Handle lease termination with confirmation"""
        # Calculate penalty (5% of monthly rent)
        penalty = round(rent * 0.05, 2)
        
        # Show confirmation dialog with details
        confirm = messagebox.askyesno(
            "Confirm Lease Termination", 
            f"Are you sure you want to terminate this lease?\n\n"
            f"Lease ID: #{lease_id}\n"
            f"Monthly Rent: £{rent:,.2f}\n"
            f"Early Termination Penalty (5%): £{penalty:,.2f}\n\n"
            f"⚠ This action is immediate and cannot be undone."
        )
        
        if confirm:
            try:
                # Call database service to terminate the lease
                from database.lease_service import update_lease_early_termination
                update_lease_early_termination(lease_id, penalty)
                
                # Show success message
                messagebox.showinfo(
                    "Success", 
                    f"Lease #{lease_id} has been terminated.\n"
                    f"Penalty charged: £{penalty:,.2f}\n\n"
                    f"Please vacate the property within 30 days."
                )
                
                # Refresh the list to show updated status
                self._load_data()
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not terminate lease: {e}")

def create_page(parent, user_info):
    """Factory function to create the appropriate lease page based on user role"""
    if not user_info or len(user_info) < 5:
        from main.lease_page import LeaseManagerPage
        return LeaseManagerPage(parent, user_info=None).frame
    
    role = user_info[4] 
    if role == "Tenant":
        page = TenantLeaseExitPage(parent, user_info=user_info)
        page.frame.on_show = page.on_show
        return page.frame
    else:
        from main.lease_page import LeaseManagerPage
        return LeaseManagerPage(parent, user_info=user_info).frame
