# ============================================================================
# MAINTENANCE METRICS MODULE
# Displays performance metrics and analytics for maintenance operations
# ============================================================================

import tkinter as tk
from tkinter import ttk


class MetricsSummaryPanel:
    """Display summary metrics in a compact grid"""
    
    def __init__(self, parent, metrics_data):
        self.parent = parent
        self.metrics_data = metrics_data
        self._render()
    
    def _render(self):
        """Build summary metrics display"""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        wrapper = tk.Frame(self.parent, bg="white")
        wrapper.pack(fill="x", padx=10, pady=10)
        
        # Title
        tk.Label(
            wrapper, text="Maintenance Performance Metrics",
            font=("Arial", 14, "bold"), bg="white",
        ).pack(pady=(0, 10))
        
        # Unpack metrics data
        total, completed, pending, in_progress, avg_time = self.metrics_data
        
        # Create grid of metrics
        grid = tk.Frame(wrapper, bg="white")
        grid.pack(fill="x", pady=5)
        
        metrics = [
            ("Total Requests", total, "#3B86FF"),
            ("Completed", completed, "#28a745"),
            ("Pending", pending, "#ffc107"),
            ("In Progress", in_progress, "#17a2b8"),
            ("Avg Days", avg_time, "#6c757d"),
        ]
        
        # Create metric cards
        for idx, (label, value, color) in enumerate(metrics):
            card = tk.Frame(grid, bg=color, bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=5, sticky="ew")
            
            # Value
            tk.Label(
                card, text=str(value),
                font=("Arial", 20, "bold"), bg=color, fg="white",
            ).pack(pady=(8, 3))
            
            # Label
            tk.Label(
                card, text=label,
                font=("Arial", 9), bg=color, fg="white",
            ).pack(pady=(0, 8))
            
            grid.grid_columnconfigure(idx, weight=1)


class CostAnalysisPanel:
    """Display cost analysis metrics in compact format"""
    
    def __init__(self, parent, cost_data):
        self.parent = parent
        self.cost_data = cost_data
        self._render()
    
    def _render(self):
        """Build cost analysis display"""
        wrapper = tk.Frame(self.parent, bg="white", bd=1, relief="solid")
        wrapper.pack(fill="x", padx=10, pady=5)
        
        # Title
        tk.Label(
            wrapper, text="Cost Analysis",
            font=("Arial", 12, "bold"), bg="white",
        ).pack(pady=(8, 5))
        
        # Unpack cost data
        total, avg, max_cost, min_cost = self.cost_data
        
        # Create grid layout
        grid = tk.Frame(wrapper, bg="white")
        grid.pack(fill="x", padx=10, pady=(0, 8))
        
        costs = [
            ("Total:", f"£{total:,.2f}"),
            ("Average:", f"£{avg:,.2f}"),
            ("Max:", f"£{max_cost:,.2f}"),
            ("Min:", f"£{min_cost:,.2f}"),
        ]
        
        # Display cost metrics
        for idx, (label, value) in enumerate(costs):
            tk.Label(
                grid, text=label,
                font=("Arial", 10, "bold"), bg="white",
            ).grid(row=0, column=idx*2, sticky="e", padx=(5, 2))
            
            tk.Label(
                grid, text=value,
                font=("Arial", 10), bg="white",
            ).grid(row=0, column=idx*2+1, sticky="w", padx=(0, 10))


class StaffPerformancePanel:
    """Display top staff performance in compact table"""
    
    def __init__(self, parent, staff_data):
        self.parent = parent
        self.staff_data = staff_data
        self._render()
    
    def _render(self):
        """Build staff performance display"""
        wrapper = tk.Frame(self.parent, bg="white", bd=1, relief="solid")
        wrapper.pack(fill="x", padx=10, pady=5)
        
        # Title
        tk.Label(
            wrapper, text="Top Staff Performance",
            font=("Arial", 12, "bold"), bg="white",
        ).pack(pady=(8, 5))
        
        # Create tree view table
        tree = ttk.Treeview(
            wrapper,
            columns=("staff", "tasks", "avg_days"),
            show="headings",
            height=5,
        )
        
        tree.heading("staff", text="Staff Member")
        tree.heading("tasks", text="Tasks")
        tree.heading("avg_days", text="Avg Days")
        
        tree.column("staff", width=150, anchor="w")
        tree.column("tasks", width=80, anchor="center")
        tree.column("avg_days", width=80, anchor="center")
        
        tree.pack(fill="x", padx=10, pady=(0, 8))
        
        # Insert staff data
        for row in self.staff_data:
            tree.insert("", "end", values=row)


class RecentCompletionsPanel:
    """Display recent completions in compact table"""
    
    def __init__(self, parent, recent_data):
        self.parent = parent
        self.recent_data = recent_data
        self._render()
    
    def _render(self):
        """Build recent completions display"""
        wrapper = tk.Frame(self.parent, bg="white", bd=1, relief="solid")
        wrapper.pack(fill="x", padx=10, pady=5)
        
        # Title
        tk.Label(
            wrapper, text="Recent Completions",
            font=("Arial", 12, "bold"), bg="white",
        ).pack(pady=(8, 5))
        
        # Create tree view table
        tree = ttk.Treeview(
            wrapper,
            columns=("id", "issue", "tenant", "date", "days"),
            show="headings",
            height=5,
        )
        
        tree.heading("id", text="ID")
        tree.heading("issue", text="Issue")
        tree.heading("tenant", text="Tenant")
        tree.heading("date", text="Completed")
        tree.heading("days", text="Days")
        
        tree.column("id", width=50, anchor="center")
        tree.column("issue", width=180, anchor="w")
        tree.column("tenant", width=120, anchor="w")
        tree.column("date", width=90, anchor="center")
        tree.column("days", width=60, anchor="center")
        
        tree.pack(fill="x", padx=10, pady=(0, 8))
        
        # Insert recent data
        for row in self.recent_data:
            tree.insert("", "end", values=row)