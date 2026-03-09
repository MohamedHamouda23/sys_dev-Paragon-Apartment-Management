import tkinter as tk
<<<<<<< HEAD
from tkinter import messagebox
from datetime import date, timedelta

from core.helpers import (
    create_button, create_frame, clear_frame,
    styled_label, form_field, form_dropdown, card,
    BG, ACCENT, FONT_TITLE, FONT_LABEL,
)

from core.lease_service import (
    fetch_leases, fetch_tenants, fetch_available_apartments,
    create_lease, build_tenant_map, build_apartment_map,
)

class LeaseManagerPage:

    def __init__(self, parent):
        self.parent = parent
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        self.create_buttons()
        self.refresh_leases()


    def create_buttons(self):
        for text, command in [
            ("Add Lease",       self.on_add_lease),
            ("Remove Lease",    self.show_remove_lease),
            ("Track Lease",     self.refresh_leases),
        ]:
            create_button(
                self.btns_inner_frame,
                text=text,
                width=150,
                height=50,
                bg="#3B86FF",
                fg="white",
                command=command,
                next_window_func=None,
                current_window=None,
            ).pack(side="left", padx=15, pady=50)

    
    def refresh_leases(self):
        clear_frame(self.box_frame)
        leases = fetch_leases()

        container = card(self.box_frame)
        styled_label(container, "Lease Agreements", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))

        if not leases:
            styled_label(
                container,
                "Registered leases will appear here",
                font=FONT_LABEL,
                fg="#888",
            ).pack(expand=True, pady=20)
            return


        for lease in leases:
            (l_id, _apt_id, _ten_id,
             tenant_name, apt_display,
             start, end, rent, status) = lease

            STATUS_COLORS = {
                "Active":     "#2E7D32",
                "Terminated": "#C62828",
                "Expired":    "#F57F17",
            }
            color = STATUS_COLORS.get(status, "#333")

            text = (
                f"[{l_id}]  {tenant_name}  |  {apt_display}  |  "
                f"{start} → {end}  |  £{float(rent):,.2f}/mo  |  {status}"
            )
            row = tk.Frame(container, bg=BG)
            row.pack(fill="x", pady=3, anchor="w")
            styled_label(row, text, fg=color).pack(anchor="w", padx=4)

    # ---------------------------------------------------
    def on_add_lease(self):
        AddLeaseStepper(self.box_frame, self.refresh_leases)

    # ---------------------------------------------------
    def show_remove_lease(self):
        RemoveLeaseStepper(self.box_frame, self.refresh_leases)


class AddLeaseStepper:

    def __init__(self, parent, refresh_callback):
        self.box_frame        = parent
        self.refresh_callback = refresh_callback

        tenants    = fetch_tenants()
        apartments = fetch_available_apartments()

        self.tenant_map   = build_tenant_map(tenants)
        self.tenant_names = list(self.tenant_map.keys())

        self.apt_map      = build_apartment_map(apartments)
        self.apt_displays = list(self.apt_map.keys())

        self.step_tenant()

    # ---------------------------------------------------
    def step_tenant(self):
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        styled_label(container, "Add Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 3 — Select Tenant", fg="#888").pack(pady=(0, 8))

        if not self.tenant_names:
            styled_label(container, "No tenants registered yet.", fg="#C62828").pack(pady=10)
            return

        tenant_cb = form_dropdown(container, "Tenant", self.tenant_names)

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

    # ---------------------------------------------------
    def step_apartment(self, tenant_name):
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        styled_label(container, "Add Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 3 — Select Apartment", fg="#888").pack(pady=(0, 8))
        styled_label(container, f"Tenant: {tenant_name}", fg="#555").pack(anchor="w")

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

        apt_cb = form_dropdown(container, "Apartment (Vacant)", self.apt_displays)

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

    # ---------------------------------------------------
    def step_details(self, tenant_name, apt_display):
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        styled_label(container, "Add Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 3 of 3 — Lease Details", fg="#888").pack(pady=(0, 8))

        info = tk.Frame(container, bg="#F5F5F5", padx=12, pady=8)
        info.pack(fill="x", pady=(0, 12))
        styled_label(info, f"{tenant_name}  ·  {apt_display}", fg="#555").pack(anchor="w")

        start_entry = form_field(container, "Start Date (YYYY-MM-DD)", [0])
        end_entry   = form_field(container, "End Date (YYYY-MM-DD)",   [0])
        rent_entry  = form_field(container, "Monthly Rent (£)",         [0])

        # Pre-fill start/end with sensible defaults
        today = date.today()
        start_entry.insert(0, str(today))
        end_entry.insert(0, str(today.replace(year=today.year + 1)))

        def submit():
            try:
                tenant_id = self.tenant_map[tenant_name]
                apt_id    = self.apt_map[apt_display]
                create_lease(
                    apt_id,
                    tenant_id,
                    start_entry.get(),
                    end_entry.get(),
                    rent_entry.get(),
                )
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    "✓  Lease created successfully!",
                    fg="#2E7D32",
                ).pack(expand=True)
                self.box_frame.after(1200, self.refresh_callback)
            except Exception as e:
                messagebox.showerror("Error", str(e))

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


class RemoveLeaseStepper:
    """
    Step 1 — pick a lease to remove.
    Step 2 — confirm (shows early-termination penalty if applicable).
    """

    def __init__(self, parent, refresh_callback):
        self.box_frame        = parent
        self.refresh_callback = refresh_callback
        self.step_select()

   
    def step_select(self):
        clear_frame(self.box_frame)
        container = card(self.box_frame)

        styled_label(container, "Remove Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 1 of 2 — Select Lease", fg="#888").pack(pady=(0, 8))

        leases = fetch_leases()
        if not leases:
            styled_label(container, "No leases found.", fg="#C62828").pack(pady=10)
            return

        self.lease_map = {
            f"[{l[0]}] {l[3]} – {l[4]}": l
            for l in leases
        }
        lease_cb = form_dropdown(container, "Lease", list(self.lease_map.keys()))

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


    def step_confirm(self, lease):
        (l_id, _apt_id, _ten_id,
         tenant_name, apt_display,
         start, end, rent, status) = lease

        is_early  = date.fromisoformat(str(end)) > date.today()
        penalty   = round(float(rent) * 0.05, 2) if is_early else 0.00
        vacate    = str(date.today() + timedelta(days=30)) if is_early else str(end)

        clear_frame(self.box_frame)
        container = card(self.box_frame)

        styled_label(container, "Remove Lease", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))
        styled_label(container, "Step 2 of 2 — Confirm", fg="#888").pack(pady=(0, 8))

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

        if is_early:
            styled_label(
                container,
                "⚠  Early termination — 1 month notice + 5% penalty applies.",
                fg="#C62828",
            ).pack(pady=(0, 8))

        def confirm():
            try:
                from core.database import update_lease_early_termination
                if is_early:
                    update_lease_early_termination(l_id, penalty)
                else:
                    update_lease_early_termination(l_id, 0)
                clear_frame(self.box_frame)
                styled_label(
                    self.box_frame,
                    f"✓  Lease removed.  {'Penalty: £' + str(penalty) if is_early else ''}",
                    fg="#2E7D32",
                ).pack(expand=True)
                self.box_frame.after(1500, self.refresh_callback)
            except Exception as e:
                messagebox.showerror("Error", str(e))

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


def create_page(parent):
    return LeaseManagerPage(parent).frame