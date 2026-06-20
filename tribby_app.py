import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
import csv

# For charts
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

CATEGORY_COLORS = [
    "#00F0FF", "#A855F7", "#22C55E", "#F59E0B", "#EF4444",
    "#3B82F6", "#EC4899", "#84CC16", "#FB923C", "#14B8A6",
    "#8B5CF6", "#F43F5E",
]

DEFAULT_CATEGORIES = ["Food", "Bills", "Transport", "Shopping", "Entertainment", "Health", "Other"]

RECUR_INTERVALS = ["Daily", "Weekly", "Monthly", "Yearly"]


# ------------------------------------------------------------
# Data Manager (JSON storage)
# ------------------------------------------------------------
class DataManager:
    def __init__(self):
        self.transactions_file = "tribby_transactions.json"
        self.budget_file = "tribby_budget.json"
        self.goals_file = "tribby_goals.json"
        self.category_budgets_file = "tribby_category_budgets.json"
        self.recurring_file = "tribby_recurring.json"
        self.settings_file = "tribby_settings.json"
        self.load_all()
        self.process_recurring()

    def load_all(self):
        self.transactions = self._load_json(self.transactions_file, [])
        self.budget = self._load_json(self.budget_file, 20000)
        self.goals = self._load_json(self.goals_file, [])
        self.category_budgets = self._load_json(self.category_budgets_file, {})
        self.recurring = self._load_json(self.recurring_file, [])
        self.settings = self._load_json(self.settings_file, {"theme": "dark"})

    def _load_json(self, file, default):
        if os.path.exists(file):
            try:
                with open(file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return default
        return default

    def _save_json(self, file, data):
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

    def save_transactions(self): self._save_json(self.transactions_file, self.transactions)
    def save_budget(self): self._save_json(self.budget_file, self.budget)
    def save_goals(self): self._save_json(self.goals_file, self.goals)
    def save_category_budgets(self): self._save_json(self.category_budgets_file, self.category_budgets)
    def save_recurring(self): self._save_json(self.recurring_file, self.recurring)
    def save_settings(self): self._save_json(self.settings_file, self.settings)

    # ---------- Transactions ----------
    def add_transaction(self, description, amount, category, date=None):
        txn = {
            "id": int(datetime.now().timestamp() * 1000) + len(self.transactions),
            "description": description,
            "amount": amount,
            "category": category,
            "date": (date or datetime.now()).isoformat()
        }
        self.transactions.append(txn)
        self.save_transactions()
        return txn

    def update_transaction(self, txn_id, description, amount, category):
        for t in self.transactions:
            if t["id"] == txn_id:
                t["description"] = description
                t["amount"] = amount
                t["category"] = category
                break
        self.save_transactions()

    def delete_transaction(self, txn_id):
        self.transactions = [t for t in self.transactions if t["id"] != txn_id]
        self.save_transactions()

    def clear_transactions(self):
        self.transactions = []
        self.save_transactions()

    def all_categories(self):
        cats = set(DEFAULT_CATEGORIES)
        for t in self.transactions:
            if t.get("category"):
                cats.add(t["category"])
        for r in self.recurring:
            if r.get("category"):
                cats.add(r["category"])
        return sorted(cats)

    # ---------- Goals ----------
    def add_goal(self, name, target):
        goal = {
            "id": int(datetime.now().timestamp() * 1000),
            "name": name,
            "target": target,
            "current": 0,
            "createdAt": datetime.now().isoformat()
        }
        self.goals.append(goal)
        self.save_goals()
        return goal

    def update_goal(self, goal_id, added):
        for g in self.goals:
            if g["id"] == goal_id:
                g["current"] = min(g["target"], max(0, g["current"] + added))
                break
        self.save_goals()

    def delete_goal(self, goal_id):
        self.goals = [g for g in self.goals if g["id"] != goal_id]
        self.save_goals()

    # ---------- Category budgets ----------
    def set_category_budget(self, category, amount):
        if amount <= 0:
            self.category_budgets.pop(category, None)
        else:
            self.category_budgets[category] = amount
        self.save_category_budgets()

    # ---------- Recurring ----------
    def add_recurring(self, description, amount, category, interval, next_date):
        rec = {
            "id": int(datetime.now().timestamp() * 1000) + len(self.recurring),
            "description": description,
            "amount": amount,
            "category": category,
            "interval": interval,
            "next_date": next_date.isoformat(),
        }
        self.recurring.append(rec)
        self.save_recurring()
        return rec

    def delete_recurring(self, rec_id):
        self.recurring = [r for r in self.recurring if r["id"] != rec_id]
        self.save_recurring()

    @staticmethod
    def _advance(date, interval):
        if interval == "Daily":
            return date + timedelta(days=1)
        if interval == "Weekly":
            return date + timedelta(weeks=1)
        if interval == "Monthly":
            month = date.month + 1
            year = date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(date.day, 28)
            return date.replace(year=year, month=month, day=day)
        if interval == "Yearly":
            try:
                return date.replace(year=date.year + 1)
            except ValueError:
                return date.replace(year=date.year + 1, day=28)
        return date

    def process_recurring(self):
        """Auto-generate transactions for any recurring items due up to today."""
        now = datetime.now()
        changed = False
        for r in self.recurring:
            next_date = datetime.fromisoformat(r["next_date"])
            guard = 0
            while next_date <= now and guard < 500:
                self.add_transaction(r["description"], r["amount"], r["category"], date=next_date)
                next_date = self._advance(next_date, r["interval"])
                changed = True
                guard += 1
            r["next_date"] = next_date.isoformat()
        if changed:
            self.save_recurring()


# ------------------------------------------------------------
# Theme palettes
# ------------------------------------------------------------
THEMES = {
    "dark": {
        "mode": "dark",
        "bg": "#0D1117",
        "card_bg": "#161B22",
        "card_bg_light": "#1F242F",
        "sidebar": "#0A0E12",
        "border": "#30363D",
        "text": "#FFFFFF",
        "text_muted": "#8B949E",
        "cyan": "#00F0FF",
        "purple": "#A855F7",
        "success": "#22C55E",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "row_alt": "#1A1F29",
    },
    "light": {
        "mode": "light",
        "bg": "#F4F6FA",
        "card_bg": "#FFFFFF",
        "card_bg_light": "#FFFFFF",
        "sidebar": "#E9EDF5",
        "border": "#D7DCE5",
        "text": "#0D1117",
        "text_muted": "#5C6573",
        "cyan": "#0891B2",
        "purple": "#7C3AED",
        "success": "#16A34A",
        "danger": "#DC2626",
        "warning": "#D97706",
        "row_alt": "#F0F2F7",
    },
}


# ------------------------------------------------------------
# Main Application
# ------------------------------------------------------------
class TribbyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tribby - Modern Finance Tracker")
        self.geometry("1500x950")
        self.minsize(1300, 800)

        self.data = DataManager()
        self.current_view = "dashboard"
        self.filter_var = ctk.StringVar(value="all")
        self.category_filter_var = ctk.StringVar(value="All")
        self.search_var = ctk.StringVar(value="")
        self.sort_var = ctk.StringVar(value="Date (newest)")
        self.editing_txn_id = None

        theme_name = self.data.settings.get("theme", "dark")
        if theme_name not in THEMES:
            theme_name = "dark"
        self.theme_name = theme_name
        self.apply_theme_palette()

        ctk.set_appearance_mode(THEMES[self.theme_name]["mode"])
        ctk.set_default_color_theme("blue")

        self.setup_ui()
        self.refresh_all()

    def apply_theme_palette(self):
        t = THEMES[self.theme_name]
        self.bg = t["bg"]
        self.card_bg = t["card_bg"]
        self.card_bg_light = t["card_bg_light"]
        self.sidebar_color = t["sidebar"]
        self.border = t["border"]
        self.text = t["text"]
        self.text_muted = t["text_muted"]
        self.cyan = t["cyan"]
        self.purple = t["purple"]
        self.success = t["success"]
        self.danger = t["danger"]
        self.warning = t["warning"]
        self.row_alt = t["row_alt"]

    def category_color(self, category):
        cats = self.data.all_categories()
        if category in cats:
            idx = cats.index(category) % len(CATEGORY_COLORS)
        else:
            idx = hash(category) % len(CATEGORY_COLORS)
        return CATEGORY_COLORS[idx]

    # ------------------------------------------------------------
    # UI SHELL
    # ------------------------------------------------------------
    def setup_ui(self):
        self.configure(fg_color=self.bg)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 40))
        ctk.CTkLabel(logo_frame, text="\U0001F4B0", font=("Segoe UI", 34)).pack()
        ctk.CTkLabel(logo_frame, text="T R I B B Y", font=("Segoe UI", 18, "bold"), text_color=self.cyan).pack()
        ctk.CTkLabel(logo_frame, text="modern finance tracker", font=("Segoe UI", 10), text_color=self.text_muted).pack()

        # Navigation buttons
        nav_buttons = [
            ("\U0001F4CA Dashboard", "dashboard", self.show_dashboard),
            ("\U0001F4DD Transactions", "transactions", self.show_transactions),
            ("\U0001F4B0 Budget & Goals", "budget", self.show_budget_goals),
            ("\U0001F501 Recurring", "recurring", self.show_recurring),
        ]
        self.nav_btns = {}
        for text, view, cmd in nav_buttons:
            btn = ctk.CTkButton(self.sidebar, text=text, command=cmd, fg_color="transparent",
                                 text_color=self.text_muted, hover_color=self.card_bg_light,
                                 anchor="w", corner_radius=8, height=40, font=("Segoe UI", 13))
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_btns[view] = btn

        # Theme toggle + footer
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", pady=20, fill="x", padx=15)

        theme_label = "\u2600\ufe0f Light Mode" if self.theme_name == "dark" else "\U0001F319 Dark Mode"
        self.theme_btn = ctk.CTkButton(bottom_frame, text=theme_label, command=self.toggle_theme,
                                        fg_color="transparent", text_color=self.text_muted,
                                        hover_color=self.card_bg_light, border_width=1, border_color=self.border,
                                        corner_radius=8, height=36, font=("Segoe UI", 12))
        self.theme_btn.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(bottom_frame, text="(c) 2025 Tribby", font=("Segoe UI", 10), text_color=self.text_muted).pack()

        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color=self.bg, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        self.show_dashboard()

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.data.settings["theme"] = self.theme_name
        self.data.save_settings()
        ctk.set_appearance_mode(THEMES[self.theme_name]["mode"])
        self.apply_theme_palette()
        self.rebuild_ui()

    def rebuild_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self.setup_ui()
        self.refresh_all()

    def set_active_nav(self, active):
        for view, btn in self.nav_btns.items():
            if view == active:
                btn.configure(fg_color=self.card_bg_light, text_color=self.cyan)
            else:
                btn.configure(fg_color="transparent", text_color=self.text_muted)

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    # ------------------------------------------------------------
    # DASHBOARD VIEW
    # ------------------------------------------------------------
    def show_dashboard(self):
        self.current_view = "dashboard"
        self.set_active_nav("dashboard")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        self.dashboard_scroll = scroll

        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Financial Dashboard", font=("Segoe UI", 26, "bold"), text_color=self.text).pack(anchor="w")
        ctk.CTkLabel(header, text="Your money at a glance", font=("Segoe UI", 13), text_color=self.text_muted).pack(anchor="w")

        # Stats row
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)

        self.stat_vars = {
            "balance": ctk.StringVar(value="\u20b10"),
            "income": ctk.StringVar(value="\u20b10"),
            "expenses": ctk.StringVar(value="\u20b10"),
            "budget_usage": ctk.StringVar(value="0%")
        }
        stats = [
            ("\U0001F4B0 Balance", "balance", self.cyan),
            ("\U0001F4C8 Income", "income", self.success),
            ("\U0001F4C9 Expenses", "expenses", self.danger),
            ("\U0001F3AF Budget Used", "budget_usage", self.warning)
        ]
        for i, (label, key, color) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=label, font=("Segoe UI", 13), text_color=self.text_muted).pack(pady=(12, 5))
            ctk.CTkLabel(card, textvariable=self.stat_vars[key], font=("Segoe UI", 28, "bold"), text_color=color).pack(pady=(0, 12))

        # Charts row: trends + category breakdown
        charts_row = ctk.CTkFrame(scroll, fg_color="transparent")
        charts_row.pack(fill="x", pady=10)
        charts_row.grid_columnconfigure(0, weight=2)
        charts_row.grid_columnconfigure(1, weight=1)

        trend_card = ctk.CTkFrame(charts_row, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        trend_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        ctk.CTkLabel(trend_card, text="Monthly Trends", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 2))
        ctk.CTkLabel(trend_card, text="Income vs Expenses over time", font=("Segoe UI", 11), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(0, 8))
        self.chart_frame = ctk.CTkFrame(trend_card, fg_color=self.card_bg_light)
        self.chart_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.chart_frame.configure(height=260)
        self.chart_frame.pack_propagate(False)

        cat_card = ctk.CTkFrame(charts_row, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        cat_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(cat_card, text="Spending by Category", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 2))
        ctk.CTkLabel(cat_card, text="This month's expenses", font=("Segoe UI", 11), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(0, 8))
        self.category_chart_frame = ctk.CTkFrame(cat_card, fg_color=self.card_bg_light)
        self.category_chart_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.category_chart_frame.configure(height=260)
        self.category_chart_frame.pack_propagate(False)

        # Net worth trend (full width)
        net_card = ctk.CTkFrame(scroll, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        net_card.pack(fill="x", pady=10)
        ctk.CTkLabel(net_card, text="Net Worth Over Time", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 2))
        ctk.CTkLabel(net_card, text="Cumulative balance from all transactions", font=("Segoe UI", 11), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(0, 8))
        self.networth_chart_frame = ctk.CTkFrame(net_card, fg_color=self.card_bg_light)
        self.networth_chart_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.networth_chart_frame.configure(height=220)
        self.networth_chart_frame.pack_propagate(False)

        # Budget alerts + quick stats
        info_card = ctk.CTkFrame(scroll, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        info_card.pack(fill="x", pady=10)
        self.info_label = ctk.CTkLabel(info_card, text="", font=("Segoe UI", 13), text_color=self.text_muted, justify="left")
        self.info_label.pack(pady=18, padx=20, anchor="w")

        self.alerts_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.alerts_frame.pack(fill="x", pady=(0, 10))

        self.update_dashboard()

    # ------------------------------------------------------------
    # TRANSACTIONS VIEW
    # ------------------------------------------------------------
    def show_transactions(self):
        self.current_view = "transactions"
        self.set_active_nav("transactions")
        self.clear_content()
        self.editing_txn_id = None

        # Header
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Transaction Management", font=("Segoe UI", 26, "bold"), text_color=self.text).pack(anchor="w")
        ctk.CTkLabel(header, text="Add, edit, and track your transactions", font=("Segoe UI", 13), text_color=self.text_muted).pack(anchor="w")

        # Add/Edit transaction card
        self.add_card = ctk.CTkFrame(self.content_frame, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        self.add_card.pack(fill="x", pady=10)
        self.add_card_title = ctk.CTkLabel(self.add_card, text="Add New Transaction", font=("Segoe UI", 14, "bold"), text_color=self.cyan)
        self.add_card_title.pack(anchor="w", padx=20, pady=(10, 5))

        form = ctk.CTkFrame(self.add_card, fg_color="transparent")
        form.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(form, text="Description:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.desc_entry = ctk.CTkEntry(form, width=280, placeholder_text="e.g., Coffee, Salary")
        self.desc_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(form, text="Amount:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.amount_entry = ctk.CTkEntry(form, width=120, placeholder_text="0.00")
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5)

        self.trans_type = ctk.StringVar(value="expense")
        ctk.CTkRadioButton(form, text="Income", variable=self.trans_type, value="income", text_color=self.success).grid(row=0, column=4, padx=8)
        ctk.CTkRadioButton(form, text="Expense", variable=self.trans_type, value="expense", text_color=self.danger).grid(row=0, column=5, padx=8)

        ctk.CTkLabel(form, text="Category:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=0, column=6, padx=5, pady=5, sticky="e")
        self.cat_entry = ctk.CTkComboBox(form, width=160, values=self.data.all_categories())
        self.cat_entry.set("")
        self.cat_entry.grid(row=0, column=7, padx=5, pady=5)

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=8, pady=10)
        self.add_btn = ctk.CTkButton(btn_row, text="\u2795 Add Transaction", command=self.add_transaction,
                                      fg_color=self.cyan, text_color="#000000", font=("Segoe UI", 11, "bold"), height=32, width=180)
        self.add_btn.pack(side="left", padx=5)
        self.cancel_edit_btn = ctk.CTkButton(btn_row, text="Cancel", command=self.cancel_edit,
                                              fg_color="#2A2D37", hover_color="#3A3D47", height=32, width=100)
        # hidden until editing

        # Transaction list card
        list_card = ctk.CTkFrame(self.content_frame, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        list_card.pack(fill="both", expand=True, pady=(10, 20))
        ctk.CTkLabel(list_card, text="Transaction History", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 5))

        # Summary bar
        self.summary_frame = ctk.CTkFrame(list_card, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.border)
        self.summary_frame.pack(fill="x", padx=20, pady=(5, 10))
        self.summary_label = ctk.CTkLabel(self.summary_frame, text="", font=("Segoe UI", 13, "bold"), text_color=self.text)
        self.summary_label.pack(pady=8)

        # Controls: search, filters, sort
        control_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(control_frame, text="Search:", font=("Segoe UI", 11), text_color=self.text_muted).pack(side="left", padx=(0, 5))
        search_entry = ctk.CTkEntry(control_frame, width=180, placeholder_text="Description...", textvariable=self.search_var)
        search_entry.pack(side="left", padx=(0, 15))
        self.search_var.trace_add("write", lambda *a: self.refresh_transactions())

        ctk.CTkLabel(control_frame, text="Category:", font=("Segoe UI", 11), text_color=self.text_muted).pack(side="left", padx=(0, 5))
        cat_options = ["All"] + self.data.all_categories()
        cat_filter = ctk.CTkComboBox(control_frame, width=140, values=cat_options, variable=self.category_filter_var,
                                      command=lambda v: self.refresh_transactions())
        cat_filter.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(control_frame, text="Sort:", font=("Segoe UI", 11), text_color=self.text_muted).pack(side="left", padx=(0, 5))
        sort_options = ["Date (newest)", "Date (oldest)", "Amount (high-low)", "Amount (low-high)", "Category"]
        sort_combo = ctk.CTkComboBox(control_frame, width=160, values=sort_options, variable=self.sort_var,
                                      command=lambda v: self.refresh_transactions())
        sort_combo.pack(side="left", padx=(0, 15))

        export_btn = ctk.CTkButton(control_frame, text="\U0001F4E5 Export CSV", command=self.export_csv, fg_color="#2A2D37", hover_color="#3A3D47", width=110)
        export_btn.pack(side="right", padx=5)
        clear_btn = ctk.CTkButton(control_frame, text="\U0001F5D1\ufe0f Clear All", command=self.clear_all_transactions, fg_color="#4A1A2A", hover_color="#6A2A3A", text_color=self.danger, width=100)
        clear_btn.pack(side="right", padx=5)

        # Income/Expense filter
        filter_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(filter_frame, text="Show:", font=("Segoe UI", 11), text_color=self.text_muted).pack(side="left")
        for f, label in [("all", "All"), ("income", "Income"), ("expense", "Expense")]:
            rb = ctk.CTkRadioButton(filter_frame, text=label, variable=self.filter_var, value=f, command=self.refresh_transactions)
            rb.pack(side="left", padx=12)

        # Column headers
        col_header = ctk.CTkFrame(list_card, fg_color="transparent")
        col_header.pack(fill="x", padx=20, pady=(5, 0))
        for txt, w in [("Date", 100), ("Description", 280), ("Category", 150), ("Amount", 140), ("", 110)]:
            ctk.CTkLabel(col_header, text=txt, font=("Segoe UI", 11, "bold"), text_color=self.text_muted, width=w, anchor="w").pack(side="left", padx=5)

        # Scrollable transaction rows
        self.txn_scroll = ctk.CTkScrollableFrame(list_card, fg_color=self.card_bg, corner_radius=12)
        self.txn_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        self.refresh_transactions()

    def get_filtered_sorted_transactions(self):
        filter_val = self.filter_var.get()
        cat_val = self.category_filter_var.get()
        search_val = self.search_var.get().strip().lower()

        filtered = []
        for t in self.data.transactions:
            if filter_val == "income" and t["amount"] <= 0:
                continue
            if filter_val == "expense" and t["amount"] >= 0:
                continue
            if cat_val != "All" and t.get("category") != cat_val:
                continue
            if search_val and search_val not in t["description"].lower():
                continue
            filtered.append(t)

        sort_val = self.sort_var.get()
        if sort_val == "Date (newest)":
            filtered.sort(key=lambda x: x["id"], reverse=True)
        elif sort_val == "Date (oldest)":
            filtered.sort(key=lambda x: x["id"])
        elif sort_val == "Amount (high-low)":
            filtered.sort(key=lambda x: x["amount"], reverse=True)
        elif sort_val == "Amount (low-high)":
            filtered.sort(key=lambda x: x["amount"])
        elif sort_val == "Category":
            filtered.sort(key=lambda x: (x.get("category") or "").lower())
        return filtered

    def refresh_transactions(self):
        if not hasattr(self, "txn_scroll"):
            return
        filtered = self.get_filtered_sorted_transactions()

        total_income = sum(t["amount"] for t in filtered if t["amount"] > 0)
        total_expense = abs(sum(t["amount"] for t in filtered if t["amount"] < 0))
        net = total_income - total_expense
        self.summary_label.configure(
            text=f"\U0001F4CA {len(filtered)} transactions  |  \U0001F4C8 Income: \u20b1{total_income:,.2f}  |  \U0001F4C9 Expenses: \u20b1{total_expense:,.2f}  |  \U0001F4B0 Net: \u20b1{net:,.2f}"
        )

        for w in self.txn_scroll.winfo_children():
            w.destroy()

        if not filtered:
            ctk.CTkLabel(self.txn_scroll, text="No transactions match your filters.", font=("Segoe UI", 13), text_color=self.text_muted).pack(pady=30)
            return

        for i, t in enumerate(filtered[:200]):
            row_color = self.card_bg if i % 2 == 0 else self.row_alt
            row = ctk.CTkFrame(self.txn_scroll, fg_color=row_color, corner_radius=8)
            row.pack(fill="x", pady=2)

            date_str = datetime.fromisoformat(t["date"]).strftime("%Y-%m-%d")
            ctk.CTkLabel(row, text=date_str, font=("Segoe UI", 11), text_color=self.text_muted, width=100, anchor="w").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=t["description"], font=("Segoe UI", 12), text_color=self.text, width=280, anchor="w").pack(side="left", padx=5)

            cat = t.get("category", "")
            cat_badge = ctk.CTkLabel(row, text=cat, font=("Segoe UI", 10, "bold"), text_color="#000000",
                                      fg_color=self.category_color(cat), corner_radius=8, width=110, height=22)
            cat_badge_holder = ctk.CTkFrame(row, fg_color="transparent", width=150)
            cat_badge_holder.pack(side="left", padx=5)
            cat_badge.pack(in_=cat_badge_holder, anchor="w")

            sign = "+" if t["amount"] > 0 else "-"
            amount_color = self.success if t["amount"] > 0 else self.danger
            ctk.CTkLabel(row, text=f"{sign}\u20b1{abs(t['amount']):,.2f}", font=("Segoe UI", 12, "bold"),
                         text_color=amount_color, width=140, anchor="w").pack(side="left", padx=5)

            action_frame = ctk.CTkFrame(row, fg_color="transparent", width=110)
            action_frame.pack(side="left", padx=5)
            edit_btn = ctk.CTkButton(action_frame, text="\u270F\ufe0f", width=32, height=28, fg_color="transparent",
                                      text_color=self.cyan, hover_color=self.card_bg_light,
                                      command=lambda tid=t["id"]: self.start_edit_transaction(tid))
            edit_btn.pack(side="left", padx=2)
            del_btn = ctk.CTkButton(action_frame, text="\U0001F5D1\ufe0f", width=32, height=28, fg_color="transparent",
                                     text_color=self.danger, hover_color="#4A1A2A",
                                     command=lambda tid=t["id"]: self.delete_transaction_by_id(tid))
            del_btn.pack(side="left", padx=2)

        if len(filtered) > 200:
            ctk.CTkLabel(self.txn_scroll, text=f"Showing first 200 of {len(filtered)} transactions.",
                         font=("Segoe UI", 11), text_color=self.text_muted).pack(pady=10)

    def delete_transaction_by_id(self, txn_id):
        txn = next((t for t in self.data.transactions if t["id"] == txn_id), None)
        if not txn:
            return
        if messagebox.askyesno("Delete", f"Delete '{txn['description']}'?"):
            self.data.delete_transaction(txn_id)
            if self.editing_txn_id == txn_id:
                self.cancel_edit()
            self.refresh_all()

    def start_edit_transaction(self, txn_id):
        txn = next((t for t in self.data.transactions if t["id"] == txn_id), None)
        if not txn:
            return
        self.editing_txn_id = txn_id
        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, txn["description"])
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, f"{abs(txn['amount'])}")
        self.trans_type.set("income" if txn["amount"] > 0 else "expense")
        self.cat_entry.set(txn.get("category", ""))

        self.add_card_title.configure(text="Edit Transaction")
        self.add_btn.configure(text="\U0001F4BE Save Changes")
        self.cancel_edit_btn.pack(side="left", padx=5)

    def cancel_edit(self):
        self.editing_txn_id = None
        self.desc_entry.delete(0, "end")
        self.amount_entry.delete(0, "end")
        self.cat_entry.set("")
        self.trans_type.set("expense")
        self.add_card_title.configure(text="Add New Transaction")
        self.add_btn.configure(text="\u2795 Add Transaction")
        self.cancel_edit_btn.pack_forget()

    def clear_all_transactions(self):
        if messagebox.askyesno("Clear All", "Delete ALL transactions? Cannot be undone."):
            self.data.clear_transactions()
            self.refresh_all()

    def export_csv(self):
        if not self.data.transactions:
            messagebox.showinfo("Export", "No transactions to export.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Description", "Category", "Amount", "Type"])
                for t in self.data.transactions:
                    date = datetime.fromisoformat(t["date"]).strftime("%Y-%m-%d")
                    typ = "Income" if t["amount"] > 0 else "Expense"
                    writer.writerow([date, t["description"], t["category"], abs(t["amount"]), typ])
            messagebox.showinfo("Export", f"Exported to {filepath}")

    # ---------- Add / Edit transaction submit ----------
    def add_transaction(self):
        desc = self.desc_entry.get().strip()
        amt_str = self.amount_entry.get().strip()
        cat = self.cat_entry.get().strip()
        if not desc or not amt_str or not cat:
            messagebox.showerror("Missing info", "Please fill all fields.")
            return
        try:
            amt = float(amt_str)
        except ValueError:
            messagebox.showerror("Invalid amount", "Amount must be a number.")
            return
        if amt <= 0:
            messagebox.showerror("Invalid amount", "Amount must be greater than zero.")
            return
        if self.trans_type.get() == "expense":
            amt = -abs(amt)
        else:
            amt = abs(amt)

        if self.editing_txn_id is not None:
            self.data.update_transaction(self.editing_txn_id, desc, amt, cat)
            self.cancel_edit()
            messagebox.showinfo("Success", "Transaction updated.")
        else:
            self.data.add_transaction(desc, amt, cat)
            self.desc_entry.delete(0, "end")
            self.amount_entry.delete(0, "end")
            self.cat_entry.set("")
            messagebox.showinfo("Success", "Transaction added.")

        self.refresh_all()
        if self.current_view == "transactions":
            self.show_transactions()

    # ------------------------------------------------------------
    # BUDGET & GOALS VIEW
    # ------------------------------------------------------------
    def show_budget_goals(self):
        self.current_view = "budget"
        self.set_active_nav("budget")
        self.clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Budget & Goals", font=("Segoe UI", 26, "bold"), text_color=self.text).pack(anchor="w")
        ctk.CTkLabel(header, text="Plan your spending and track savings", font=("Segoe UI", 13), text_color=self.text_muted).pack(anchor="w")

        # Two columns
        columns = ctk.CTkFrame(scroll, fg_color="transparent")
        columns.pack(fill="both", expand=True, pady=10)
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=1)

        # LEFT: Overall Budget
        left = ctk.CTkFrame(columns, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        left.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        ctk.CTkLabel(left, text="Monthly Budget", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 5))
        ctk.CTkLabel(left, text="Set your overall spending limit", font=("Segoe UI", 11), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(0, 8))

        self.budget_display = ctk.CTkLabel(left, text=f"\u20b1{self.data.budget:,.2f}", font=("Segoe UI", 24, "bold"), text_color=self.text)
        self.budget_display.pack(pady=5)

        quick_frame = ctk.CTkFrame(left, fg_color="transparent")
        quick_frame.pack(pady=8)
        for amt in [10000, 20000, 30000, 50000]:
            btn = ctk.CTkButton(quick_frame, text=f"\u20b1{amt:,}", command=lambda a=amt: self.set_budget(a), fg_color="#2A2D37", width=90, height=32)
            btn.pack(side="left", padx=5)

        slider_frame = ctk.CTkFrame(left, fg_color="transparent")
        slider_frame.pack(fill="x", padx=20, pady=15)
        self.budget_slider = ctk.CTkSlider(slider_frame, from_=5000, to=150000, number_of_steps=145, command=self.set_budget_slider)
        self.budget_slider.pack(fill="x")
        self.budget_slider.set(self.data.budget)

        self.budget_progress = ctk.CTkProgressBar(left, height=12, corner_radius=6)
        self.budget_progress.pack(pady=12, padx=20, fill="x")
        self.budget_progress.set(0)

        self.budget_stats = ctk.CTkLabel(left, text="", font=("Segoe UI", 11), text_color=self.text_muted)
        self.budget_stats.pack(pady=(0, 10))

        # Category budgets section
        ctk.CTkLabel(left, text="Category Budgets", font=("Segoe UI", 13, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(10, 5))
        ctk.CTkLabel(left, text="Set spending limits per category", font=("Segoe UI", 11), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(0, 8))

        cat_form = ctk.CTkFrame(left, fg_color="transparent")
        cat_form.pack(fill="x", padx=20, pady=(0, 10))
        self.cat_budget_combo = ctk.CTkComboBox(cat_form, width=140, values=self.data.all_categories())
        self.cat_budget_combo.pack(side="left", padx=(0, 8))
        self.cat_budget_entry = ctk.CTkEntry(cat_form, width=110, placeholder_text="Amount")
        self.cat_budget_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(cat_form, text="Set", width=60, height=28, fg_color=self.purple,
                       command=self.set_category_budget_from_form).pack(side="left")

        self.cat_budgets_container = ctk.CTkFrame(left, fg_color="transparent")
        self.cat_budgets_container.pack(fill="x", padx=20, pady=(0, 20))

        # RIGHT: Savings Goals
        right = ctk.CTkFrame(columns, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        right.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        ctk.CTkLabel(right, text="Savings Goals", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 5))
        ctk.CTkLabel(right, text="Track your progress", font=("Segoe UI", 11), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(0, 8))

        add_goal_frame = ctk.CTkFrame(right, fg_color="transparent")
        add_goal_frame.pack(fill="x", padx=20, pady=(5, 15))
        self.goal_name_entry = ctk.CTkEntry(add_goal_frame, width=200, placeholder_text="Goal name")
        self.goal_name_entry.pack(side="left", padx=5)
        self.goal_target_entry = ctk.CTkEntry(add_goal_frame, width=120, placeholder_text="Target amount")
        self.goal_target_entry.pack(side="left", padx=5)
        ctk.CTkButton(add_goal_frame, text="\u2795 Create Goal", command=self.add_goal, fg_color=self.purple,
                       text_color="#FFFFFF", font=("Segoe UI", 11)).pack(side="left", padx=10)

        self.goals_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent", height=400)
        self.goals_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.goals_container = self.goals_scroll

        self.update_budget_ui()
        self.refresh_category_budgets()
        self.refresh_goals()

    def set_budget_slider(self, value):
        self.set_budget(int(value))

    def set_category_budget_from_form(self):
        cat = self.cat_budget_combo.get().strip()
        amt_str = self.cat_budget_entry.get().strip()
        if not cat:
            messagebox.showerror("Error", "Choose a category.")
            return
        try:
            amt = float(amt_str) if amt_str else 0
        except ValueError:
            messagebox.showerror("Error", "Invalid amount.")
            return
        if amt <= 0:
            messagebox.showerror("Error", "Enter an amount greater than zero.")
            return
        self.data.set_category_budget(cat, amt)
        self.cat_budget_entry.delete(0, "end")
        self.refresh_category_budgets()
        if self.current_view == "dashboard":
            self.update_dashboard()

    def refresh_category_budgets(self):
        if not hasattr(self, "cat_budgets_container"):
            return
        for w in self.cat_budgets_container.winfo_children():
            w.destroy()

        if not self.data.category_budgets:
            ctk.CTkLabel(self.cat_budgets_container, text="No category budgets set yet.",
                          font=("Segoe UI", 11), text_color=self.text_muted).pack(pady=10)
            return

        spent_by_cat = self.spending_by_category_this_month()
        for cat, limit in self.data.category_budgets.items():
            spent = spent_by_cat.get(cat, 0)
            usage = min(spent / limit, 1.0) if limit > 0 else 0

            row = ctk.CTkFrame(self.cat_budgets_container, fg_color=self.card_bg, corner_radius=10, border_width=1, border_color=self.border)
            row.pack(fill="x", pady=4)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 0))
            badge = ctk.CTkLabel(top, text=cat, font=("Segoe UI", 11, "bold"), text_color="#000000",
                                  fg_color=self.category_color(cat), corner_radius=8, width=100, height=22)
            badge.pack(side="left")
            ctk.CTkLabel(top, text=f"\u20b1{spent:,.0f} / \u20b1{limit:,.0f}", font=("Segoe UI", 11), text_color=self.text_muted).pack(side="left", padx=10)

            del_btn = ctk.CTkButton(top, text="\u2716", width=26, height=26, fg_color="transparent",
                                     text_color=self.danger, hover_color="#4A1A2A",
                                     command=lambda c=cat: self.delete_category_budget(c))
            del_btn.pack(side="right")

            bar_color = self.danger if usage >= 1.0 else (self.warning if usage >= 0.8 else self.success)
            prog = ctk.CTkProgressBar(row, height=8, corner_radius=4, progress_color=bar_color)
            prog.pack(fill="x", padx=12, pady=(5, 10))
            prog.set(usage)

    def delete_category_budget(self, category):
        self.data.set_category_budget(category, 0)
        self.refresh_category_budgets()
        if self.current_view == "dashboard":
            self.update_dashboard()

    def spending_by_category_this_month(self):
        now = datetime.now()
        totals = {}
        for t in self.data.transactions:
            if t["amount"] >= 0:
                continue
            d = datetime.fromisoformat(t["date"])
            if d.year == now.year and d.month == now.month:
                cat = t.get("category", "Other")
                totals[cat] = totals.get(cat, 0) + abs(t["amount"])
        return totals

    # ------------------------------------------------------------
    # RECURRING VIEW
    # ------------------------------------------------------------
    def show_recurring(self):
        self.current_view = "recurring"
        self.set_active_nav("recurring")
        self.clear_content()

        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Recurring Transactions", font=("Segoe UI", 26, "bold"), text_color=self.text).pack(anchor="w")
        ctk.CTkLabel(header, text="Automate bills, subscriptions, and regular income", font=("Segoe UI", 13), text_color=self.text_muted).pack(anchor="w")

        # Add recurring form
        add_card = ctk.CTkFrame(self.content_frame, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        add_card.pack(fill="x", pady=10)
        ctk.CTkLabel(add_card, text="New Recurring Item", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(10, 5))

        form = ctk.CTkFrame(add_card, fg_color="transparent")
        form.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(form, text="Description:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.rec_desc_entry = ctk.CTkEntry(form, width=220, placeholder_text="e.g., Rent, Netflix, Salary")
        self.rec_desc_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(form, text="Amount:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.rec_amount_entry = ctk.CTkEntry(form, width=110, placeholder_text="0.00")
        self.rec_amount_entry.grid(row=0, column=3, padx=5, pady=5)

        self.rec_type = ctk.StringVar(value="expense")
        ctk.CTkRadioButton(form, text="Income", variable=self.rec_type, value="income", text_color=self.success).grid(row=0, column=4, padx=8)
        ctk.CTkRadioButton(form, text="Expense", variable=self.rec_type, value="expense", text_color=self.danger).grid(row=0, column=5, padx=8)

        ctk.CTkLabel(form, text="Category:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.rec_cat_entry = ctk.CTkComboBox(form, width=160, values=self.data.all_categories())
        self.rec_cat_entry.set("")
        self.rec_cat_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(form, text="Repeats:", font=("Segoe UI", 11), text_color=self.text_muted).grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.rec_interval = ctk.CTkComboBox(form, width=110, values=RECUR_INTERVALS)
        self.rec_interval.set("Monthly")
        self.rec_interval.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkButton(form, text="\u2795 Add Recurring", command=self.add_recurring_item, fg_color=self.cyan,
                       text_color="#000000", font=("Segoe UI", 11, "bold"), height=32).grid(row=1, column=4, columnspan=2, padx=8, pady=5, sticky="w")

        # List of recurring items
        list_card = ctk.CTkFrame(self.content_frame, fg_color=self.card_bg_light, corner_radius=16, border_width=1, border_color=self.border)
        list_card.pack(fill="both", expand=True, pady=(10, 20))
        ctk.CTkLabel(list_card, text="Active Recurring Items", font=("Segoe UI", 14, "bold"), text_color=self.cyan).pack(anchor="w", padx=20, pady=(12, 5))

        self.recurring_scroll = ctk.CTkScrollableFrame(list_card, fg_color=self.card_bg, corner_radius=12)
        self.recurring_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        self.refresh_recurring()

    def add_recurring_item(self):
        desc = self.rec_desc_entry.get().strip()
        amt_str = self.rec_amount_entry.get().strip()
        cat = self.rec_cat_entry.get().strip()
        interval = self.rec_interval.get()
        if not desc or not amt_str or not cat:
            messagebox.showerror("Missing info", "Please fill all fields.")
            return
        try:
            amt = float(amt_str)
        except ValueError:
            messagebox.showerror("Invalid amount", "Amount must be a number.")
            return
        if amt <= 0:
            messagebox.showerror("Invalid amount", "Amount must be greater than zero.")
            return
        if self.rec_type.get() == "expense":
            amt = -abs(amt)
        else:
            amt = abs(amt)

        self.data.add_recurring(desc, amt, cat, interval, datetime.now())
        self.rec_desc_entry.delete(0, "end")
        self.rec_amount_entry.delete(0, "end")
        self.rec_cat_entry.set("")
        self.refresh_recurring()
        messagebox.showinfo("Success", f"'{desc}' will repeat {interval.lower()}.")

    def refresh_recurring(self):
        if not hasattr(self, "recurring_scroll"):
            return
        for w in self.recurring_scroll.winfo_children():
            w.destroy()

        if not self.data.recurring:
            ctk.CTkLabel(self.recurring_scroll, text="\u2728 No recurring items yet. Add one above! \u2728",
                          font=("Segoe UI", 13), text_color=self.text_muted).pack(pady=30)
            return

        for r in self.data.recurring:
            row = ctk.CTkFrame(self.recurring_scroll, fg_color=self.card_bg_light, corner_radius=10, border_width=1, border_color=self.border)
            row.pack(fill="x", pady=4)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=12, pady=10)
            ctk.CTkLabel(left, text=r["description"], font=("Segoe UI", 12, "bold"), text_color=self.text).pack(anchor="w")
            next_date = datetime.fromisoformat(r["next_date"]).strftime("%Y-%m-%d")
            ctk.CTkLabel(left, text=f"{r['interval']}  |  Next: {next_date}  |  {r['category']}",
                          font=("Segoe UI", 10), text_color=self.text_muted).pack(anchor="w")

            amount_color = self.success if r["amount"] > 0 else self.danger
            sign = "+" if r["amount"] > 0 else "-"
            ctk.CTkLabel(row, text=f"{sign}\u20b1{abs(r['amount']):,.2f}", font=("Segoe UI", 13, "bold"),
                          text_color=amount_color).pack(side="left", padx=10)

            ctk.CTkButton(row, text="\U0001F5D1\ufe0f", width=36, height=32, fg_color="transparent",
                           text_color=self.danger, hover_color="#4A1A2A",
                           command=lambda rid=r["id"]: self.delete_recurring_item(rid)).pack(side="right", padx=10)

    def delete_recurring_item(self, rec_id):
        if messagebox.askyesno("Delete", "Remove this recurring item? Past transactions will remain."):
            self.data.delete_recurring(rec_id)
            self.refresh_recurring()

    # ------------------------------------------------------------
    # Core logic & refresh methods
    # ------------------------------------------------------------
    def refresh_all(self):
        self.update_stats()
        if self.current_view == "dashboard":
            self.update_dashboard()
        elif self.current_view == "transactions":
            self.refresh_transactions()
        elif self.current_view == "budget":
            self.update_budget_ui()
            self.refresh_category_budgets()
            self.refresh_goals()
        elif self.current_view == "recurring":
            self.refresh_recurring()

    def update_stats(self):
        incomes = [t["amount"] for t in self.data.transactions if t["amount"] > 0]
        expenses = [t["amount"] for t in self.data.transactions if t["amount"] < 0]
        total_income = sum(incomes)
        total_expense = abs(sum(expenses))
        balance = total_income - total_expense
        spent = total_expense
        usage = (spent / self.data.budget * 100) if self.data.budget > 0 else 0
        if hasattr(self, "stat_vars"):
            self.stat_vars["balance"].set(f"\u20b1{balance:,.2f}")
            self.stat_vars["income"].set(f"\u20b1{total_income:,.2f}")
            self.stat_vars["expenses"].set(f"\u20b1{total_expense:,.2f}")
            self.stat_vars["budget_usage"].set(f"{usage:.1f}%")

    def update_dashboard(self):
        self.update_stats()
        self.update_dashboard_chart()
        self.update_category_chart()
        self.update_networth_chart()
        self.update_alerts()
        txn_count = len(self.data.transactions)
        goal_count = len(self.data.goals)
        total_saved = sum(g["current"] for g in self.data.goals)
        self.info_label.configure(
            text=f"\U0001F4CA {txn_count} transactions recorded  |  \U0001F3AF {goal_count} active goals  |  \U0001F4B0 \u20b1{total_saved:,.2f} saved towards goals"
        )

    def update_alerts(self):
        if not hasattr(self, "alerts_frame"):
            return
        for w in self.alerts_frame.winfo_children():
            w.destroy()

        alerts = []
        total_expense = abs(sum(t["amount"] for t in self.data.transactions if t["amount"] < 0))
        if self.data.budget > 0:
            usage = total_expense / self.data.budget
            if usage >= 1.0:
                alerts.append((f"\u26A0\ufe0f You've exceeded your overall budget ({usage*100:.0f}% used).", self.danger))
            elif usage >= 0.8:
                alerts.append((f"\u26A0\ufe0f You're at {usage*100:.0f}% of your overall budget.", self.warning))

        spent_by_cat = self.spending_by_category_this_month()
        for cat, limit in self.data.category_budgets.items():
            spent = spent_by_cat.get(cat, 0)
            if limit <= 0:
                continue
            usage = spent / limit
            if usage >= 1.0:
                alerts.append((f"\u26A0\ufe0f '{cat}' budget exceeded ({usage*100:.0f}% used this month).", self.danger))
            elif usage >= 0.8:
                alerts.append((f"\u26A0\ufe0f '{cat}' spending at {usage*100:.0f}% of its monthly budget.", self.warning))

        for g in self.data.goals:
            if g["target"] > 0 and g["current"] >= g["target"]:
                alerts.append((f"\U0001F389 Goal '{g['name']}' completed!", self.success))

        if not alerts:
            return

        for text, color in alerts[:5]:
            banner = ctk.CTkFrame(self.alerts_frame, fg_color=self.card_bg_light, corner_radius=10, border_width=1, border_color=color)
            banner.pack(fill="x", pady=4)
            ctk.CTkLabel(banner, text=text, font=("Segoe UI", 12, "bold"), text_color=color).pack(padx=15, pady=8, anchor="w")

    def update_dashboard_chart(self):
        if not hasattr(self, "chart_frame"):
            return
        for w in self.chart_frame.winfo_children():
            w.destroy()
        monthly = {}
        for t in self.data.transactions:
            date = datetime.fromisoformat(t["date"])
            month_key = date.strftime("%B %Y")
            if month_key not in monthly:
                monthly[month_key] = {"income": 0, "expenses": 0}
            if t["amount"] > 0:
                monthly[month_key]["income"] += t["amount"]
            else:
                monthly[month_key]["expenses"] += abs(t["amount"])
        sorted_months = sorted(monthly.keys(), key=lambda x: datetime.strptime(x, "%B %Y"))
        last_months = sorted_months[-6:] if len(sorted_months) >= 6 else sorted_months
        if not last_months:
            ctk.CTkLabel(self.chart_frame, text="Add transactions to see trends", font=("Segoe UI", 13), text_color=self.text_muted).pack(expand=True)
            return
        incomes = [monthly[m]["income"] for m in last_months]
        expenses = [monthly[m]["expenses"] for m in last_months]
        labels = [m.split()[0][:3] + " '" + m.split()[1][2:] for m in last_months]

        fig = Figure(figsize=(8, 2.4), dpi=100, facecolor=self.card_bg_light)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.card_bg)
        ax.plot(labels, incomes, marker="o", color=self.cyan, linewidth=2.5, label="Income")
        ax.plot(labels, expenses, marker="s", color=self.danger, linewidth=2.5, label="Expenses")
        ax.fill_between(labels, incomes, color=self.cyan, alpha=0.15)
        ax.fill_between(labels, expenses, color=self.danger, alpha=0.15)
        ax.tick_params(colors=self.text_muted, labelsize=10)
        ax.grid(True, linestyle="--", alpha=0.2, color=self.border)
        ax.legend(loc="upper left", facecolor=self.card_bg_light, labelcolor=self.text, fontsize=10)
        ax.set_ylim(bottom=0)
        for spine in ax.spines.values():
            spine.set_color(self.border)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_category_chart(self):
        if not hasattr(self, "category_chart_frame"):
            return
        for w in self.category_chart_frame.winfo_children():
            w.destroy()

        spent_by_cat = self.spending_by_category_this_month()
        if not spent_by_cat:
            ctk.CTkLabel(self.category_chart_frame, text="No expenses this month yet",
                          font=("Segoe UI", 13), text_color=self.text_muted).pack(expand=True)
            return

        sorted_items = sorted(spent_by_cat.items(), key=lambda x: x[1], reverse=True)
        labels = [c for c, _ in sorted_items]
        values = [v for _, v in sorted_items]
        colors = [self.category_color(c) for c in labels]

        fig = Figure(figsize=(4.5, 2.4), dpi=100, facecolor=self.card_bg_light)
        ax = fig.add_subplot(111)
        wedges, _ = ax.pie(values, colors=colors, startangle=90,
                            wedgeprops={"width": 0.42, "edgecolor": self.card_bg_light, "linewidth": 2})
        total = sum(values)
        ax.text(0, 0, f"\u20b1{total:,.0f}", ha="center", va="center", fontsize=12, fontweight="bold", color=self.text)
        ax.legend(wedges, [f"{l} ({v/total*100:.0f}%)" for l, v in zip(labels, values)],
                  loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8,
                  facecolor=self.card_bg_light, labelcolor=self.text, frameon=False)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.category_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_networth_chart(self):
        if not hasattr(self, "networth_chart_frame"):
            return
        for w in self.networth_chart_frame.winfo_children():
            w.destroy()

        if not self.data.transactions:
            ctk.CTkLabel(self.networth_chart_frame, text="Add transactions to see your net worth trend",
                          font=("Segoe UI", 13), text_color=self.text_muted).pack(expand=True)
            return

        sorted_txns = sorted(self.data.transactions, key=lambda x: x["id"])
        running_total = 0
        points = []
        for t in sorted_txns:
            running_total += t["amount"]
            d = datetime.fromisoformat(t["date"])
            points.append((d, running_total))

        # Downsample to last 60 points for readability
        if len(points) > 60:
            points = points[-60:]

        dates = [p[0] for p in points]
        balances = [p[1] for p in points]

        fig = Figure(figsize=(12, 2), dpi=100, facecolor=self.card_bg_light)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.card_bg)
        line_color = self.success if balances[-1] >= 0 else self.danger
        ax.plot(dates, balances, color=line_color, linewidth=2.5)
        ax.fill_between(dates, balances, color=line_color, alpha=0.15)
        ax.axhline(0, color=self.text_muted, linewidth=1, linestyle="--", alpha=0.5)
        ax.tick_params(colors=self.text_muted, labelsize=9)
        ax.grid(True, linestyle="--", alpha=0.2, color=self.border)
        fig.autofmt_xdate(rotation=0, ha="center")
        for spine in ax.spines.values():
            spine.set_color(self.border)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.networth_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------- Budget ----------
    def set_budget(self, amount):
        if amount >= 1000:
            self.data.budget = amount
            self.data.save_budget()
            self.update_budget_ui()
            self.update_stats()
            if self.current_view == "dashboard":
                self.update_dashboard()

    def update_budget_ui(self):
        if not hasattr(self, "budget_display"):
            return
        self.budget_display.configure(text=f"\u20b1{self.data.budget:,.2f}")
        self.budget_slider.set(self.data.budget)
        spent = abs(sum(t["amount"] for t in self.data.transactions if t["amount"] < 0))
        usage = (spent / self.data.budget) if self.data.budget > 0 else 0
        bar_color = self.danger if usage >= 1.0 else (self.warning if usage >= 0.8 else self.cyan)
        self.budget_progress.configure(progress_color=bar_color)
        self.budget_progress.set(min(usage, 1.0))
        remaining = self.data.budget - spent
        self.budget_stats.configure(text=f"Spent: \u20b1{spent:,.2f}  |  Remaining: \u20b1{remaining:,.2f}")

    # ---------- Goals ----------
    def add_goal(self):
        name = self.goal_name_entry.get().strip()
        target_str = self.goal_target_entry.get().strip()
        if not name or not target_str:
            messagebox.showerror("Error", "Please fill both fields.")
            return
        try:
            target = float(target_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid target amount.")
            return
        if target <= 0:
            messagebox.showerror("Error", "Target must be greater than zero.")
            return
        self.data.add_goal(name, target)
        self.goal_name_entry.delete(0, "end")
        self.goal_target_entry.delete(0, "end")
        self.refresh_goals()
        if self.current_view == "dashboard":
            self.update_dashboard()

    def refresh_goals(self):
        if not hasattr(self, "goals_container"):
            return
        for w in self.goals_container.winfo_children():
            w.destroy()
        if not self.data.goals:
            ctk.CTkLabel(self.goals_container, text="\u2728 No goals yet. Create one above! \u2728",
                          font=("Segoe UI", 13), text_color=self.text_muted).pack(pady=30)
            return
        for goal in self.data.goals:
            g_frame = ctk.CTkFrame(self.goals_container, fg_color=self.card_bg, corner_radius=12, border_width=1, border_color=self.border)
            g_frame.pack(fill="x", pady=8, padx=5)

            header = ctk.CTkFrame(g_frame, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(8, 0))
            ctk.CTkLabel(header, text=goal["name"], font=("Segoe UI", 12, "bold"), text_color=self.cyan).pack(side="left")
            del_btn = ctk.CTkButton(header, text="\u2716", width=30, height=30, fg_color="transparent",
                                     text_color=self.danger, hover_color="#4A1A2A",
                                     command=lambda gid=goal["id"]: self.delete_goal(gid))
            del_btn.pack(side="right")

            percent = (goal["current"] / goal["target"] * 100) if goal["target"] > 0 else 0
            ctk.CTkLabel(g_frame, text=f"\u20b1{goal['current']:,.0f} / \u20b1{goal['target']:,.0f}  ({percent:.0f}%)",
                          font=("Segoe UI", 10), text_color=self.text_muted).pack(anchor="w", padx=12)
            prog_color = self.success if percent >= 100 else self.cyan
            prog = ctk.CTkProgressBar(g_frame, height=8, corner_radius=4, progress_color=prog_color)
            prog.pack(pady=5, padx=12, fill="x")
            prog.set(min(percent / 100, 1.0))

            btn_row = ctk.CTkFrame(g_frame, fg_color="transparent")
            btn_row.pack(pady=8)
            for amt in [50, 100, 500]:
                btn = ctk.CTkButton(btn_row, text=f"+\u20b1{amt}", width=70, height=28, fg_color="#2A2D37",
                                     command=lambda a=amt, gid=goal["id"]: self.add_to_goal(gid, a))
                btn.pack(side="left", padx=4)
            custom_entry = ctk.CTkEntry(btn_row, width=100, placeholder_text="Custom")
            custom_entry.pack(side="left", padx=8)
            add_custom = ctk.CTkButton(btn_row, text="Add", width=50, height=28, fg_color=self.purple,
                                        command=lambda gid=goal["id"], e=custom_entry: self.custom_add_to_goal(gid, e))
            add_custom.pack(side="left")

    def add_to_goal(self, goal_id, amount):
        self.data.update_goal(goal_id, amount)
        self.refresh_goals()
        if self.current_view == "dashboard":
            self.update_dashboard()

    def custom_add_to_goal(self, goal_id, entry):
        try:
            amt = float(entry.get().strip())
            if amt <= 0:
                raise ValueError
            self.data.update_goal(goal_id, amt)
            entry.delete(0, "end")
            self.refresh_goals()
            if self.current_view == "dashboard":
                self.update_dashboard()
        except ValueError:
            messagebox.showerror("Error", "Enter a positive number.")

    def delete_goal(self, goal_id):
        if messagebox.askyesno("Delete Goal", "Delete this goal permanently?"):
            self.data.delete_goal(goal_id)
            self.refresh_goals()
            if self.current_view == "dashboard":
                self.update_dashboard()


# ------------------------------------------------------------
# Run
# ------------------------------------------------------------
if __name__ == "__main__":
    app = TribbyApp()
    app.mainloop()