# ============================================================================
# LEASE PAGE
# Main page for viewing and managing lease agreements
# ============================================================================

import tkinter as tk

from main.helpers import (
    create_button, create_frame, clear_frame,
    styled_label, card,
    BG, ACCENT, FONT_TITLE, FONT_LABEL,
)

from database.lease_service import fetch_leases
from modules.Lease_Management import AddLeaseStepper, RemoveLeaseStepper


class LeaseManagerPage:
    """Lease management page with add/remove/track functionality"""

    def __init__(self, parent):
        # Store parent
        self.parent = parent
        
        # Create main frame with standard layout
        self.frame, self.btns_inner_frame, self.box_frame = create_frame(parent)
        
        # Build UI components
        self.create_buttons()
        self.refresh_leases()

    # ========================================================================
    # CREATE BUTTONS
    # ========================================================================

    def create_buttons(self):
        """Create action buttons"""
        for text, command in [
            ("Add Lease",    self.on_add_lease),
            ("Remove Lease", self.show_remove_lease),
            ("Track Lease",  self.refresh_leases),
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

    # ========================================================================
    # REFRESH LEASE LIST
    # ========================================================================

    def refresh_leases(self):
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
        """Load and display all lease agreements"""
        clear_frame(self.box_frame)
        leases = fetch_leases()

        # Create lease list container
        container = card(self.box_frame)
        styled_label(container, "Lease Agreements", font=FONT_TITLE, fg="#222").pack(pady=(0, 4))
        tk.Frame(container, bg=ACCENT, height=3, width=60).pack(pady=(0, 16))

        # Show placeholder if no leases
        if not leases:
            styled_label(
                container,
                "Registered leases will appear here",
                font=FONT_LABEL,
                fg="#888",
            ).pack(expand=True, pady=20)
            return

        # Display each lease
        for lease in leases:
            (l_id, _apt_id, _ten_id,
             tenant_name, apt_display,
             start, end, rent, status) = lease

            # Status color mapping
            STATUS_COLORS = {
                "Active":     "#2E7D32",
                "Terminated": "#C62828",
                "Expired":    "#F57F17",
            }
            color = STATUS_COLORS.get(status, "#333")

            # Format lease text
            text = (
                f"[{l_id}]  {tenant_name}  |  {apt_display}  |  "
                f"{start} → {end}  |  £{float(rent):,.2f}/mo  |  {status}"
            )
            
            # Create lease row
            row = tk.Frame(container, bg=BG)
            row.pack(fill="x", pady=3, anchor="w")
            styled_label(row, text, fg=color).pack(anchor="w", padx=4)

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def on_add_lease(self):
        """Open add lease wizard"""
        AddLeaseStepper(self.box_frame, self.refresh_leases)

    def show_remove_lease(self):
        """Open remove lease wizard"""
        RemoveLeaseStepper(self.box_frame, self.refresh_leases)