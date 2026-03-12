import tkinter as tk
from tkinter import messagebox
from database.maintaince_service import get_all_requests
from main.helpers import create_button, create_scrollable_treeview, show_placeholder

from modules.Request_Management import RegisterRequestPanel

# ---------------------------------------------------------------------------
# RequestManagementPage
# Request orchestrator: handles New Request (FR4.5) and views requests.
# Layout: top action bar → scrollable table → detail panel.
# All data filtered based on user credentials and city.
# ---------------------------------------------------------------------------

class RequestManagementPage:

    def __init__(self, parent, user_info=None):
        self.parent              = parent
        self.user_info           = user_info
        self.selected_request_id = None
        self._panel              = None
        self.frame               = tk.Frame(parent, bg="#c9e4c4")
        self._build_layout()
        self._load_requests()

    # ------------------------------------------------------------------ layout

    def _build_layout(self):
        # Top button bar
        top_btn_frame = tk.Frame(self.frame, bg="#c9e4c4")
        top_btn_frame.pack(side="top", fill="x", pady=(20, 8))

        btns_inner_frame = tk.Frame(top_btn_frame, bg="#c9e4c4")
        btns_inner_frame.pack(anchor="center")

        for text, cmd, w in [
            ("New Request",          self._new_request, 140),
            ("Clear Form",           self._clear_form,  110),
        ]:
            create_button(
                btns_inner_frame, text=text, width=w, height=45,
                bg="#3B86FF", fg="white", command=cmd,
            ).pack(side="left", padx=8)

        # Main content area: table on top, detail panel below
        content_frame = tk.Frame(self.frame, bg="#c9e4c4")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        _table_wrap, self.tree = create_scrollable_treeview(
            parent   = content_frame,
            columns  = ("id", "tenant", "issue", "date_submitted", "status"),
            headings = ("Request ID", "Tenant", "Issue", "Date Submitted", "Status"),
            widths   = (90, 160, 220, 140, 120),
            anchors  = ("center", "w", "w", "center", "center"),
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Grooved white frame that hosts swappable panels
        self.detail_wrap = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
        self.detail_wrap.pack(fill="x", padx=0, pady=(10, 0))
        show_placeholder(self.detail_wrap, "Select a request or create a new one")

    # ------------------------------------------------------------------ data

    def _load_requests(self, reselect_id=None):
        """Reload the table from DB; optionally reselect a row by request_id.
        Filters data based on user's city credentials."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Pass user_info for city-based filtering
        for row in (get_all_requests(user_info=self.user_info) or []):
            self.tree.insert("", "end", values=row)

        if reselect_id is not None:
            for item in self.tree.get_children():
                if str(self.tree.item(item, "values")[0]) == str(reselect_id):
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    self.tree.see(item)
                    break

    # ------------------------------------------------------------------ events

    def _on_row_select(self, _event=None):
        """Show request selected message."""
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.selected_request_id = values[0]
        
        for widget in self.detail_wrap.winfo_children():
            widget.destroy()
        show_placeholder(self.detail_wrap, f"Request #{self.selected_request_id} selected")

    # ------------------------------------------------------------------ actions

    def _new_request(self):
        """FR4.5 — Open the registration form in the detail area."""
        # Deselect any row so the form is not tied to an existing request
        self.selected_request_id = None
        self.tree.selection_remove(self.tree.selection())
        self._panel = RegisterRequestPanel(
            parent    = self.detail_wrap,
            user_info = self.user_info,
            on_submit = self._on_request_registered,
            on_cancel = self._clear_form,
        )

    def _on_request_registered(self, new_id):
        messagebox.showinfo(
            "Success",
            f"Maintenance request #{new_id} has been registered successfully.",
        )
        self._load_requests(reselect_id=new_id)

    def _clear_form(self):
        """Deselect any row and reset the detail panel to the placeholder."""
        self.selected_request_id = None
        self._panel              = None
        self.tree.selection_remove(self.tree.selection())
        show_placeholder(self.detail_wrap, "Select a request or create a new one")
        self._load_requests()


# ---------------------------------------------------------------------------
# Page factory
# ---------------------------------------------------------------------------

def create_page(parent, user_info=None):
    return RequestManagementPage(parent, user_info=user_info).frame