"""
Tribby — Your Personal Financial Assistant
A warm, friendly desktop app that feels like a chat with a smart friend.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
import shutil
from datetime import datetime, timedelta
import csv
import threading
import random

# ── Desktop extras ────────────────────────────────────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    from plyer import notification
    HAS_NOTIFY = True
except ImportError:
    HAS_NOTIFY = False

try:
    import reportlab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ── Matplotlib ────────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches

# ── Constants ──────────────────────────────────────────────────────────────────

CATEGORY_COLORS = [
    "#00E5FF", "#CE93D8", "#69F0AE", "#FFD740", "#FF5252",
    "#82B1FF", "#FFAB40", "#F48FB1", "#80CBC4", "#E6EE9C",
    "#80DEEA", "#BCAAA4",
]

CATEGORY_EMOJIS = {
    "food": "🍱", "dining": "🍱", "restaurant": "🍱", "coffee": "☕",
    "bills": "🧾", "subscription": "🧾", "utility": "💡",
    "transport": "🚗", "car": "🚗", "fuel": "⛽", "commute": "🚌",
    "shopping": "🛍️", "market": "🛒", "cloth": "👕",
    "entertainment": "🎮", "movie": "🎬", "game": "🎮", "stream": "📺",
    "health": "💊", "med": "💊", "gym": "💪", "doctor": "🏥",
    "salary": "💰", "income": "💰", "pay": "💳", "earn": "💰",
    "home": "🏠", "rent": "🏠", "house": "🏠",
    "education": "📚", "school": "📚", "book": "📖", "tuition": "🎓",
    "travel": "✈️", "flight": "✈️", "hotel": "🏨",
    "pet": "🐾", "gift": "🎁", "present": "🎁",
    "savings": "🏦", "investment": "📈",
}

DEFAULT_CATEGORIES = ["Food", "Bills", "Transport", "Shopping", "Entertainment", "Health", "Savings", "Other"]
RECUR_INTERVALS = ["Daily", "Weekly", "Monthly", "Yearly"]

FONT_FAMILY = "Segoe UI"

# ── Motivational quotes ──────────────────────────────────────────────────────
QUOTES = [
    "A budget is telling your money where to go instead of wondering where it went.",
    "Financial freedom is available to those who learn about it and work for it.",
    "Do not save what is left after spending, but spend what is left after saving.",
    "The best investment you can make is in yourself.",
    "It's not about having a lot of money. It's about knowing how to manage it.",
]

def cat_emoji(category: str) -> str:
    cat = category.lower()
    for key, emoji in CATEGORY_EMOJIS.items():
        if key in cat:
            return emoji
    return "📦"

# ── Themes ────────────────────────────────────────────────────────────────────

THEMES = {
    "dark": {
        "mode": "dark",
        "bg":            "#0F1117",
        "card":          "#1A1D27",
        "card_light":    "#252838",
        "sidebar":       "#0A0D14",
        "border":        "#2E3250",
        "text":          "#E8EAF6",
        "text_muted":    "#8B93B8",
        "cyan":          "#00E5FF",
        "purple":        "#CE93D8",
        "success":       "#69F0AE",
        "danger":        "#FF5252",
        "warning":       "#FFD740",
        "row_alt":       "#1E2133",
        "input_bg":      "#1A1D27",
    },
    "light": {
        "mode": "light",
        "bg":            "#F4F6FB",
        "card":          "#FFFFFF",
        "card_light":    "#F0F2FA",
        "sidebar":       "#E9EDF5",
        "border":        "#D0D5E8",
        "text":          "#1A1D27",
        "text_muted":    "#6B7299",
        "cyan":          "#0097A7",
        "purple":        "#7B1FA2",
        "success":       "#2E7D32",
        "danger":        "#C62828",
        "warning":       "#F57F17",
        "row_alt":       "#EBECF5",
        "input_bg":      "#F0F2FA",
    },
}

# ── Data Manager ──────────────────────────────────────────────────────────────

class DataManager:
    def __init__(self):
        self.transactions_file    = "tribby_transactions.json"
        self.budget_file          = "tribby_budget.json"
        self.goals_file           = "tribby_goals.json"
        self.category_budgets_file= "tribby_category_budgets.json"
        self.recurring_file       = "tribby_recurring.json"
        self.settings_file        = "tribby_settings.json"
        self.load_all()
        self.process_recurring()
        self.start_backup_timer()

    def load_all(self):
        self.transactions    = self._load(self.transactions_file, [])
        self.budget          = self._load(self.budget_file, 20000)
        self.goals           = self._load(self.goals_file, [])
        self.category_budgets= self._load(self.category_budgets_file, {})
        self.recurring       = self._load(self.recurring_file, [])
        self.settings        = self._load(self.settings_file, {"theme": "dark", "user_name": "Friend"})

    def _load(self, file, default):
        if os.path.exists(file):
            try:
                with open(file, "r") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save(self, file, data):
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

    def save_transactions(self):  self._save(self.transactions_file, self.transactions)
    def save_budget(self):        self._save(self.budget_file, self.budget)
    def save_goals(self):         self._save(self.goals_file, self.goals)
    def save_category_budgets(self): self._save(self.category_budgets_file, self.category_budgets)
    def save_recurring(self):     self._save(self.recurring_file, self.recurring)
    def save_settings(self):      self._save(self.settings_file, self.settings)

    def start_backup_timer(self):
        def backup():
            while True:
                import time
                time.sleep(3600)
                self.create_backup()
        threading.Thread(target=backup, daemon=True).start()

    def create_backup(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            for f in [self.transactions_file, self.goals_file, self.recurring_file]:
                if os.path.exists(f):
                    shutil.copy(f, f"backup_{timestamp}_{f}")
        except Exception:
            pass

    # ── Transactions ──────────────────────────────────────────────────────────
    def add_transaction(self, description, amount, category, date=None, notes=""):
        txn = {
            "id":          int(datetime.now().timestamp() * 1000) + len(self.transactions),
            "description": description,
            "amount":      amount,
            "category":    category,
            "date":        (date or datetime.now()).isoformat(),
            "notes":       notes,
        }
        self.transactions.append(txn)
        self.save_transactions()
        return txn

    def update_transaction(self, txn_id, description, amount, category, notes=""):
        for t in self.transactions:
            if t["id"] == txn_id:
                t["description"] = description
                t["amount"]      = amount
                t["category"]    = category
                t["notes"]       = notes
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
            if t.get("category"): cats.add(t["category"])
        for r in self.recurring:
            if r.get("category"): cats.add(r["category"])
        return sorted(cats)

    # ── Goals ─────────────────────────────────────────────────────────────────
    def add_goal(self, name, target, target_date=None):
        g = {
            "id":          int(datetime.now().timestamp() * 1000),
            "name":        name,
            "target":      target,
            "current":     0,
            "createdAt":   datetime.now().isoformat(),
            "target_date": target_date,
        }
        self.goals.append(g)
        self.save_goals()
        return g

    def update_goal(self, goal_id, added):
        for g in self.goals:
            if g["id"] == goal_id:
                g["current"] = min(g["target"], max(0, g["current"] + added))
                break
        self.save_goals()

    def delete_goal(self, goal_id):
        self.goals = [g for g in self.goals if g["id"] != goal_id]
        self.save_goals()

    # ── Category budgets ──────────────────────────────────────────────────────
    def set_category_budget(self, category, amount):
        if amount <= 0:
            self.category_budgets.pop(category, None)
        else:
            self.category_budgets[category] = amount
        self.save_category_budgets()

    # ── Recurring ─────────────────────────────────────────────────────────────
    def add_recurring(self, description, amount, category, interval, next_date):
        rec = {
            "id":          int(datetime.now().timestamp() * 1000) + len(self.recurring),
            "description": description,
            "amount":      amount,
            "category":    category,
            "interval":    interval,
            "next_date":   next_date.isoformat(),
        }
        self.recurring.append(rec)
        self.save_recurring()
        return rec

    def delete_recurring(self, rec_id):
        self.recurring = [r for r in self.recurring if r["id"] != rec_id]
        self.save_recurring()

    @staticmethod
    def _advance(date, interval):
        if interval == "Daily":   return date + timedelta(days=1)
        if interval == "Weekly":  return date + timedelta(weeks=1)
        if interval == "Monthly":
            m = date.month + 1; y = date.year + (m - 1) // 12; m = (m - 1) % 12 + 1
            return date.replace(year=y, month=m, day=min(date.day, 28))
        if interval == "Yearly":
            try:    return date.replace(year=date.year + 1)
            except: return date.replace(year=date.year + 1, day=28)
        return date

    def process_recurring(self):
        now = datetime.now(); changed = False
        for r in self.recurring:
            nd = datetime.fromisoformat(r["next_date"]); guard = 0
            while nd <= now and guard < 500:
                self.add_transaction(r["description"], r["amount"], r["category"], date=nd)
                nd = self._advance(nd, r["interval"]); changed = True; guard += 1
            r["next_date"] = nd.isoformat()
        if changed: self.save_recurring()

    # ── Aggregations ──────────────────────────────────────────────────────────
    def total_income(self):   return sum(t["amount"] for t in self.transactions if t["amount"] > 0)
    def total_expenses(self): return abs(sum(t["amount"] for t in self.transactions if t["amount"] < 0))
    def balance(self):        return self.total_income() - self.total_expenses()

    def spending_by_category_this_month(self):
        now = datetime.now(); totals = {}
        for t in self.transactions:
            if t["amount"] >= 0: continue
            d = datetime.fromisoformat(t["date"])
            if d.year == now.year and d.month == now.month:
                cat = t.get("category", "Other")
                totals[cat] = totals.get(cat, 0) + abs(t["amount"])
        return totals

    def monthly_totals(self, months=6):
        monthly = {}
        for t in self.transactions:
            d = datetime.fromisoformat(t["date"])
            k = d.strftime("%b '%y")
            if k not in monthly: monthly[k] = {"income": 0, "expense": 0, "sort": d.year * 12 + d.month}
            if t["amount"] > 0: monthly[k]["income"] += t["amount"]
            else:               monthly[k]["expense"] += abs(t["amount"])
        keys = sorted(monthly, key=lambda k: monthly[k]["sort"])[-months:]
        return [(k, monthly[k]["income"], monthly[k]["expense"]) for k in keys]

    def net_worth_series(self, max_pts=80):
        sorted_t = sorted(self.transactions, key=lambda x: x["id"])
        pts = []; running = 0
        for t in sorted_t:
            running += t["amount"]
            pts.append((datetime.fromisoformat(t["date"]), running))
        return pts[-max_pts:] if len(pts) > max_pts else pts

    def import_csv(self, filepath):
        added = skipped = 0
        try:
            with open(filepath, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        desc  = row.get("Description", "").strip()
                        cat   = row.get("Category", "Other").strip()
                        amt   = float(row.get("Amount", 0))
                        typ   = row.get("Type", "Expense").strip().lower()
                        date_str = row.get("Date", "").strip()
                        date  = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
                        if not desc or amt == 0: skipped += 1; continue
                        signed = abs(amt) if typ == "income" else -abs(amt)
                        self.add_transaction(desc, signed, cat, date=date)
                        added += 1
                    except Exception:
                        skipped += 1
        except Exception:
            return 0, 0
        return added, skipped

    # ── User settings ────────────────────────────────────────────────────────
    def get_user_name(self):
        return self.settings.get("user_name", "Friend")

    def set_user_name(self, name):
        self.settings["user_name"] = name
        self.save_settings()

# ── Main Application ──────────────────────────────────────────────────────────

class TribbyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Tribby — Your Personal Financial Assistant")
        self.geometry("1560x960")
        self.minsize(1200, 720)

        self.data = DataManager()
        self.current_view = "dashboard"
        self.editing_txn_id = None
        self.theme_name = self.data.settings.get("theme", "dark")
        self._apply_palette()
        ctk.set_appearance_mode(THEMES[self.theme_name]["mode"])
        ctk.set_default_color_theme("blue")

        # Check if first launch – ask for name
        if "user_name" not in self.data.settings:
            self.after(500, self._ask_name)

        # ── Keyboard shortcuts ──────────────────────────────────────────────
        self.bind_all("<Control-n>", lambda e: self._quick_add_window())
        self.bind_all("<Control-f>", lambda e: self._focus_search())
        self.bind_all("<Control-s>", lambda e: self._submit_transaction())
        self.bind_all("<Escape>", lambda e: self._cancel_edit())

        # ── UI ──────────────────────────────────────────────────────────────
        self._build_ui()
        self._init_tray()
        self.refresh_all()
        self.after(5000, self._check_notifications)

    # ── First launch: ask for name ────────────────────────────────────────────
    def _ask_name(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Welcome to Tribby!")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="What should I call you?", font=(FONT_FAMILY, 16, "bold")).pack(pady=20)
        entry = ctk.CTkEntry(dialog, placeholder_text="Your name", width=250)
        entry.pack(pady=10)
        def set_name():
            name = entry.get().strip()
            if name:
                self.data.set_user_name(name)
                self._update_greeting()
                dialog.destroy()
        ctk.CTkButton(dialog, text="Let's go!", command=set_name, fg_color=self.cyan,
                      text_color="#000000").pack(pady=10)
        entry.focus()

    def _update_greeting(self):
        if hasattr(self, "greeting_lbl"):
            name = self.data.get_user_name()
            self.greeting_lbl.configure(text=f"👋 Hello, {name}!")

    # ── Palette ───────────────────────────────────────────────────────────────
    def _apply_palette(self):
        t = THEMES[self.theme_name]
        self.bg         = t["bg"]
        self.card       = t["card"]
        self.card_light = t["card_light"]
        self.sidebar_c  = t["sidebar"]
        self.border     = t["border"]
        self.text       = t["text"]
        self.text_muted = t["text_muted"]
        self.cyan       = t["cyan"]
        self.purple     = t["purple"]
        self.success    = t["success"]
        self.danger     = t["danger"]
        self.warning    = t["warning"]
        self.row_alt    = t["row_alt"]
        self.input_bg   = t["input_bg"]

    def cat_color(self, category):
        cats = self.data.all_categories()
        idx = cats.index(category) if category in cats else hash(category)
        return CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.data.settings["theme"] = self.theme_name
        self.data.save_settings()
        ctk.set_appearance_mode(THEMES[self.theme_name]["mode"])
        self._apply_palette()
        for w in self.winfo_children(): w.destroy()
        self._build_ui()
        self.refresh_all()

    # ── Tray ──────────────────────────────────────────────────────────────────
    def _init_tray(self):
        if not HAS_TRAY: return
        try:
            image = self._create_tray_icon()
            menu = pystray.Menu(
                pystray.MenuItem("Show Tribby", self._show_window),
                pystray.MenuItem("Quick Add", self._quick_add_window),
                pystray.MenuItem("Quit", self._quit_app)
            )
            self.tray_icon = pystray.Icon("tribby", image, "Tribby", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            pass

    def _create_tray_icon(self):
        size = 64
        image = Image.new("RGB", (size, size), self.sidebar_c)
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, size-8, size-8), fill=self.cyan)
        draw.text((size//2-6, size//2-8), "₱", fill="#000000")
        return image

    def _show_window(self):
        self.deiconify()
        self.lift()

    def _quit_app(self):
        self.destroy()
        if hasattr(self, "tray_icon"):
            self.tray_icon.stop()

    # ── Notifications ─────────────────────────────────────────────────────────
    def _check_notifications(self):
        if not HAS_NOTIFY: return
        try:
            now = datetime.now()
            for r in self.data.recurring:
                nd = datetime.fromisoformat(r["next_date"])
                days = (nd - now).days
                if days == 3:
                    notification.notify(
                        title="💳 Upcoming Bill",
                        message=f"{r['description']} due in 3 days (₱{abs(r['amount']):,.2f})",
                        timeout=5
                    )
                elif days == 1:
                    notification.notify(
                        title="⏰ Bill Due Tomorrow",
                        message=f"{r['description']} due tomorrow (₱{abs(r['amount']):,.2f})",
                        timeout=5
                    )
            exp = self.data.total_expenses()
            if self.data.budget > 0 and exp > self.data.budget * 0.9:
                notification.notify(
                    title="⚠️ Budget Alert",
                    message=f"You've used {exp/self.data.budget*100:.0f}% of your monthly budget",
                    timeout=5
                )
        except Exception:
            pass
        self.after(3600000, self._check_notifications)

    # ── Shell ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.configure(fg_color=self.bg)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color=self.bg, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        self._build_status_bar()
        self.show_dashboard()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.sidebar_c)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        self.sidebar = sb

        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.pack(pady=(28, 12))
        ctk.CTkLabel(logo, text="💰", font=(FONT_FAMILY, 36)).pack()
        ctk.CTkLabel(logo, text="TRIBBY", font=(FONT_FAMILY, 20, "bold"),
                     text_color=self.cyan).pack()
        ctk.CTkLabel(logo, text="your personal assistant", font=(FONT_FAMILY, 10),
                     text_color=self.text_muted).pack()

        # Greeting
        self.greeting_lbl = ctk.CTkLabel(sb, text=f"👋 Hello, {self.data.get_user_name()}!",
                                          font=(FONT_FAMILY, 12), text_color=self.cyan)
        self.greeting_lbl.pack(pady=(4, 16))

        ctk.CTkFrame(sb, height=1, fg_color=self.border).pack(fill="x", padx=20, pady=(0, 16))

        nav_icons = ["▣", "☰", "◎", "↻"]
        nav_views = ["dashboard", "transactions", "budget", "recurring"]
        nav_labels = ["Dashboard", "Transactions", "Budget & Goals", "Recurring"]
        nav_cmds = [self.show_dashboard, self.show_transactions,
                    self.show_budget_goals, self.show_recurring]
        self.nav_btns = {}
        for label, view, cmd, icon in zip(nav_labels, nav_views, nav_cmds, nav_icons):
            btn = ctk.CTkButton(
                sb, text=f"  {icon}  {label}", command=cmd,
                fg_color="transparent", text_color=self.text_muted,
                hover_color=self.card_light, anchor="w",
                corner_radius=10, height=42,
                font=(FONT_FAMILY, 13),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_btns[view] = btn

        bottom = ctk.CTkFrame(sb, fg_color="transparent")
        bottom.pack(side="bottom", pady=20, fill="x", padx=14)
        ctk.CTkFrame(bottom, height=1, fg_color=self.border).pack(fill="x", pady=(0, 14))

        theme_icon = "☀" if self.theme_name == "dark" else "🌙"
        theme_lbl  = "Light Mode" if self.theme_name == "dark" else "Dark Mode"
        ctk.CTkButton(
            bottom, text=f"{theme_icon}  {theme_lbl}", command=self.toggle_theme,
            fg_color="transparent", text_color=self.text_muted,
            hover_color=self.card_light, border_width=1, border_color=self.border,
            corner_radius=10, height=38, font=(FONT_FAMILY, 12),
        ).pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(bottom, text="© 2025 Tribby",
                     font=(FONT_FAMILY, 10), text_color=self.text_muted).pack()

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=self.border)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_lbl = ctk.CTkLabel(self.status_bar, text="Ready", font=(FONT_FAMILY, 10))
        self.status_lbl.pack(side="left", padx=12)
        # Quick FAB‑style button on status bar (like a +)
        self.fab_btn = ctk.CTkButton(self.status_bar, text="+", width=36, height=28,
                                      command=self._quick_add_window,
                                      fg_color=self.cyan, text_color="#000000",
                                      corner_radius=30, font=(FONT_FAMILY, 16, "bold"))
        self.fab_btn.pack(side="right", padx=12)

    def _set_nav(self, active):
        for view, btn in self.nav_btns.items():
            if view == active:
                btn.configure(fg_color=self.card_light, text_color=self.cyan)
            else:
                btn.configure(fg_color="transparent", text_color=self.text_muted)

    def _clear_content(self):
        for w in self.content.winfo_children():
            if w != self.status_bar: w.destroy()

    # ── View switching ────────────────────────────────────────────────────────
    def _switch_view(self, new_view):
        self.current_view = new_view
        self._clear_content()
        if new_view == "dashboard":
            self.show_dashboard()
        elif new_view == "transactions":
            self.show_transactions()
        elif new_view == "budget":
            self.show_budget_goals()
        elif new_view == "recurring":
            self.show_recurring()
        self._set_nav(new_view)

    def _page_header(self, parent, title, subtitle):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(hdr, text=title, font=(FONT_FAMILY, 26, "bold"),
                     text_color=self.text).pack(anchor="w")
        ctk.CTkLabel(hdr, text=subtitle, font=(FONT_FAMILY, 13),
                     text_color=self.text_muted).pack(anchor="w")

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _quick_add_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Quick Add")
        win.geometry("420x350")
        win.attributes("-topmost", True)
        win.focus()

        ctk.CTkLabel(win, text="Quick Add Transaction", font=(FONT_FAMILY, 16, "bold")).pack(pady=12)

        desc = ctk.CTkEntry(win, placeholder_text="Description", width=300)
        desc.pack(pady=6)

        amt = ctk.CTkEntry(win, placeholder_text="Amount", width=300)
        amt.pack(pady=6)

        cat = ctk.CTkComboBox(win, values=self.data.all_categories(), width=300)
        cat.set("Food")
        cat.pack(pady=6)

        typ = ctk.StringVar(value="expense")
        tf = ctk.CTkFrame(win, fg_color="transparent")
        tf.pack(pady=6)
        ctk.CTkRadioButton(tf, text="Expense", variable=typ, value="expense",
                           fg_color=self.danger).pack(side="left", padx=10)
        ctk.CTkRadioButton(tf, text="Income", variable=typ, value="income",
                           fg_color=self.success).pack(side="left", padx=10)

        def add():
            d = desc.get().strip()
            a = amt.get().strip()
            c = cat.get().strip()
            if not d or not a or not c:
                messagebox.showerror("Error", "Fill all fields.")
                return
            try: am = float(a)
            except: messagebox.showerror("Error", "Invalid amount"); return
            if am <= 0: messagebox.showerror("Error", "Amount > 0"); return
            signed = am if typ.get() == "income" else -am
            self.data.add_transaction(d, signed, c)
            self.refresh_all()
            win.destroy()
            self.status_lbl.configure(text=f"Added: {d}")

        ctk.CTkButton(win, text="Add", command=add, fg_color=self.cyan,
                      text_color="#000000").pack(pady=12)

    def _focus_search(self):
        if hasattr(self, "search_entry"):
            self.search_entry.focus_set()

    # =========================================================================
    # DASHBOARD
    # =========================================================================
    def show_dashboard(self):
        self.current_view = "dashboard"
        self._set_nav("dashboard")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        self._dash_scroll = scroll

        # Greeting + quote
        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", pady=(0, 12))
        name = self.data.get_user_name()
        ctk.CTkLabel(head, text=f"👋 Welcome back, {name}!", font=(FONT_FAMILY, 24, "bold"),
                     text_color=self.text).pack(anchor="w")
        quote = random.choice(QUOTES)
        ctk.CTkLabel(head, text=f"💡 {quote}", font=(FONT_FAMILY, 13, "italic"),
                     text_color=self.text_muted).pack(anchor="w")

        # Hero stats
        hero = ctk.CTkFrame(scroll, fg_color="transparent")
        hero.pack(fill="x", pady=(0, 16))
        self._stat_vars = {
            "balance":      ctk.StringVar(value="₱0"),
            "income":       ctk.StringVar(value="₱0"),
            "expenses":     ctk.StringVar(value="₱0"),
            "budget_usage": ctk.StringVar(value="0%"),
        }
        stat_meta = [
            ("▣  Balance",     "balance",      self.cyan),
            ("↑  Income",      "income",       self.success),
            ("↓  Expenses",    "expenses",     self.danger),
            ("◎  Budget Used", "budget_usage", self.warning),
        ]
        for i, (lbl, key, color) in enumerate(stat_meta):
            hero.grid_columnconfigure(i, weight=1)
            c = ctk.CTkFrame(hero, fg_color=self.card, corner_radius=18,
                             border_width=1, border_color=self.border)
            c.grid(row=0, column=i, padx=6, sticky="nsew")
            ctk.CTkLabel(c, text=lbl, font=(FONT_FAMILY, 12),
                         text_color=self.text_muted).pack(pady=(16, 4))
            ctk.CTkLabel(c, textvariable=self._stat_vars[key],
                         font=(FONT_FAMILY, 28, "bold"),
                         text_color=color).pack(pady=(0, 16))

        # Smart Insight card (personalized)
        insight = ctk.CTkFrame(scroll, fg_color=self.card_light, corner_radius=18,
                               border_width=1, border_color=self.border)
        insight.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(insight, text="🧠 Smart Insight", font=(FONT_FAMILY, 14, "bold"),
                     text_color=self.cyan).pack(anchor="w", padx=18, pady=(12, 4))
        self.insight_lbl = ctk.CTkLabel(insight, text="Loading insights...",
                                         font=(FONT_FAMILY, 12), text_color=self.text_muted,
                                         wraplength=600, justify="left")
        self.insight_lbl.pack(anchor="w", padx=18, pady=(0, 12))
        self._update_insight()

        # Charts
        charts = ctk.CTkFrame(scroll, fg_color="transparent")
        charts.pack(fill="x", pady=(0, 12))
        charts.grid_columnconfigure(0, weight=3)
        charts.grid_columnconfigure(1, weight=2)

        flow_card = ctk.CTkFrame(charts, fg_color=self.card, corner_radius=18,
                                 border_width=1, border_color=self.border)
        flow_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        card_title(flow_card, self, "Cash Flow", "Income vs Expenses · last 6 months", "▣")
        self._flow_frame = ctk.CTkFrame(flow_card, fg_color=self.card, height=240)
        self._flow_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self._flow_frame.pack_propagate(False)

        donut_card = ctk.CTkFrame(charts, fg_color=self.card, corner_radius=18,
                                  border_width=1, border_color=self.border)
        donut_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        card_title(donut_card, self, "Spending Breakdown", "This month by category", "◎")
        self._donut_frame = ctk.CTkFrame(donut_card, fg_color=self.card, height=240)
        self._donut_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self._donut_frame.pack_propagate(False)

        nw_card = ctk.CTkFrame(scroll, fg_color=self.card, corner_radius=18,
                               border_width=1, border_color=self.border)
        nw_card.pack(fill="x", pady=(0, 12))
        card_title(nw_card, self, "Net Worth Over Time", "Cumulative balance trend", "↑")
        self._nw_frame = ctk.CTkFrame(nw_card, fg_color=self.card, height=200)
        self._nw_frame.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self._nw_frame.pack_propagate(False)

        self._alerts_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._alerts_frame.pack(fill="x", pady=(0, 4))

        self._info_card = ctk.CTkFrame(scroll, fg_color=self.card_light, corner_radius=14,
                                       border_width=1, border_color=self.border)
        self._info_card.pack(fill="x", pady=(0, 16))
        self._info_lbl = ctk.CTkLabel(self._info_card, text="", font=(FONT_FAMILY, 12),
                                       text_color=self.text_muted)
        self._info_lbl.pack(pady=12, padx=18, anchor="w")

        self._update_dashboard()

    def _update_insight(self):
        # Generate a simple insight
        exp = self.data.total_expenses()
        budget = self.data.budget
        if exp == 0:
            msg = "You haven't recorded any expenses yet. Start tracking to get insights!"
        elif budget > 0 and exp > budget * 0.9:
            msg = f"⚠️ You're close to your monthly budget! Only ₱{budget - exp:.2f} remaining."
        elif budget > 0 and exp < budget * 0.5:
            msg = "✨ You're spending less than half your budget. Keep up the great work!"
        else:
            msg = "You're making steady progress. Stay mindful of your spending."
        self.insight_lbl.configure(text=msg)

    def _update_dashboard(self):
        self._update_stats()
        self._draw_flow_chart()
        self._draw_donut()
        self._draw_networth()
        self._draw_alerts()
        n = len(self.data.transactions)
        g = len(self.data.goals)
        sv = sum(x["current"] for x in self.data.goals)
        self._info_lbl.configure(
            text=f"☰  {n} transactions recorded   ◎  {g} active goals   ₱{sv:,.2f} saved towards goals"
        )
        self._update_insight()

    def _update_stats(self):
        inc = self.data.total_income()
        exp = self.data.total_expenses()
        bal = inc - exp
        usage = (exp / self.data.budget * 100) if self.data.budget > 0 else 0
        self._stat_vars["balance"].set(f"₱{bal:,.2f}")
        self._stat_vars["income"].set(f"₱{inc:,.2f}")
        self._stat_vars["expenses"].set(f"₱{exp:,.2f}")
        self._stat_vars["budget_usage"].set(f"{usage:.1f}%")

    def _draw_flow_chart(self):
        if not hasattr(self, "_flow_frame"): return
        for w in self._flow_frame.winfo_children(): w.destroy()
        monthly = self.data.monthly_totals(months=6)
        if not monthly:
            ctk.CTkLabel(self._flow_frame, text="Add transactions to see cash flow.",
                         font=(FONT_FAMILY, 13), text_color=self.text_muted).pack(expand=True)
            return
        labels = [m[0] for m in monthly]
        incomes= [m[1] for m in monthly]
        exps   = [m[2] for m in monthly]
        x = range(len(labels))
        w = 0.35

        fig = Figure(figsize=(7, 2.4), dpi=100, facecolor=self.card)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.card_light)
        ax.bar([i - w/2 for i in x], incomes, w, color=self.success, alpha=0.85, label="Income")
        ax.bar([i + w/2 for i in x], exps,    w, color=self.danger,  alpha=0.85, label="Expenses")
        ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=9, color=self.text_muted)
        ax.tick_params(colors=self.text_muted, labelsize=9)
        ax.yaxis.tick_right(); ax.yaxis.set_tick_params(labelsize=8, colors=self.text_muted)
        ax.grid(axis="y", linestyle="--", alpha=0.18, color=self.border)
        ax.set_ylim(bottom=0)
        for spine in ax.spines.values(): spine.set_color(self.border)
        inc_patch = mpatches.Patch(color=self.success, label="Income")
        exp_patch = mpatches.Patch(color=self.danger,  label="Expenses")
        ax.legend(handles=[inc_patch, exp_patch], facecolor=self.card, labelcolor=self.text,
                  fontsize=9, loc="upper left", framealpha=0.9)
        fig.tight_layout(pad=0.6)
        canvas = FigureCanvasTkAgg(fig, master=self._flow_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_donut(self):
        if not hasattr(self, "_donut_frame"): return
        for w in self._donut_frame.winfo_children(): w.destroy()
        spent = self.data.spending_by_category_this_month()
        if not spent:
            ctk.CTkLabel(self._donut_frame, text="No expenses this month yet.",
                         font=(FONT_FAMILY, 13), text_color=self.text_muted).pack(expand=True)
            return
        sorted_items = sorted(spent.items(), key=lambda x: x[1], reverse=True)
        labels = [c for c, _ in sorted_items]
        values = [v for _, v in sorted_items]
        colors = [self.cat_color(c) for c in labels]
        total = sum(values)

        fig = Figure(figsize=(3.8, 2.4), dpi=100, facecolor=self.card)
        ax = fig.add_subplot(111)
        wedges, _ = ax.pie(values, colors=colors, startangle=90,
                           wedgeprops={"width": 0.44, "edgecolor": self.card, "linewidth": 2})
        ax.text(0, 0, f"₱{total:,.0f}", ha="center", va="center",
                fontsize=11, fontweight="bold", color=self.text)
        ax.legend(wedges, [f"{l} ({v/total*100:.0f}%)" for l, v in zip(labels, values)],
                  loc="center left", bbox_to_anchor=(0.95, 0.5),
                  fontsize=7.5, facecolor=self.card, labelcolor=self.text, frameon=False)
        fig.tight_layout(pad=0.4)
        canvas = FigureCanvasTkAgg(fig, master=self._donut_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_networth(self):
        if not hasattr(self, "_nw_frame"): return
        for w in self._nw_frame.winfo_children(): w.destroy()
        pts = self.data.net_worth_series()
        if not pts:
            ctk.CTkLabel(self._nw_frame, text="Add transactions to see your net worth trend.",
                         font=(FONT_FAMILY, 13), text_color=self.text_muted).pack(expand=True)
            return
        dates = [p[0] for p in pts]; balances = [p[1] for p in pts]
        color = self.success if balances[-1] >= 0 else self.danger

        fig = Figure(figsize=(12, 2), dpi=100, facecolor=self.card)
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.card_light)
        ax.plot(dates, balances, color=color, linewidth=2.5)
        ax.fill_between(dates, balances, color=color, alpha=0.12)
        ax.axhline(0, color=self.text_muted, linewidth=1, linestyle="--", alpha=0.4)
        ax.tick_params(colors=self.text_muted, labelsize=8)
        ax.grid(True, linestyle="--", alpha=0.15, color=self.border)
        for spine in ax.spines.values(): spine.set_color(self.border)
        fig.autofmt_xdate(rotation=0, ha="center")
        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasTkAgg(fig, master=self._nw_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_alerts(self):
        if not hasattr(self, "_alerts_frame"): return
        for w in self._alerts_frame.winfo_children(): w.destroy()
        alerts = []
        exp = self.data.total_expenses()
        if self.data.budget > 0:
            u = exp / self.data.budget
            if u >= 1.0:
                alerts.append((f"⚠  Overall budget exceeded ({u*100:.0f}% used).", self.danger))
            elif u >= 0.8:
                alerts.append((f"ℹ  You're at {u*100:.0f}% of your overall budget.", self.warning))
        spent = self.data.spending_by_category_this_month()
        for cat, limit in self.data.category_budgets.items():
            s = spent.get(cat, 0)
            if limit <= 0: continue
            u = s / limit
            if u >= 1.0:
                alerts.append((f"⚠  '{cat}' budget exceeded ({u*100:.0f}% used this month).", self.danger))
            elif u >= 0.8:
                alerts.append((f"ℹ  '{cat}' at {u*100:.0f}% of its monthly budget.", self.warning))
        for g in self.data.goals:
            if g["target"] > 0 and g["current"] >= g["target"]:
                alerts.append((f"🎉  Goal '{g['name']}' completed!", self.success))
        for text, color in alerts[:5]:
            banner = ctk.CTkFrame(self._alerts_frame, fg_color=self.card,
                                  corner_radius=12, border_width=1, border_color=color)
            banner.pack(fill="x", pady=3)
            ctk.CTkLabel(banner, text=text, font=(FONT_FAMILY, 12, "bold"),
                         text_color=color).pack(padx=16, pady=9, anchor="w")

    # =========================================================================
    # TRANSACTIONS (unchanged from previous, but kept for brevity)
    # =========================================================================
    def show_transactions(self):
        self.current_view = "transactions"
        self._set_nav("transactions")
        self._clear_content()
        self.editing_txn_id = None

        self._page_header(self.content, "Transactions", "Add, edit and track every peso")

        add_card = make_card(self.content, self, pady=(0, 10))
        card_title(add_card, self, "Quick Add / Edit", None, "☰")
        self._build_add_form(add_card)

        list_card = ctk.CTkFrame(self.content, fg_color=self.card, corner_radius=18,
                                 border_width=1, border_color=self.border)
        list_card.pack(fill="both", expand=True, pady=(0, 16))

        tb = ctk.CTkFrame(list_card, fg_color="transparent")
        tb.pack(fill="x", padx=18, pady=(12, 6))

        ctk.CTkLabel(tb, text="History", font=(FONT_FAMILY, 14, "bold"),
                     text_color=self.cyan).pack(side="left")

        right_tb = ctk.CTkFrame(tb, fg_color="transparent")
        right_tb.pack(side="right")

        self.search_entry = ctk.CTkEntry(right_tb, width=180, placeholder_text="🔍  Search…",
                                         textvariable=self.search_var, fg_color=self.input_bg,
                                         border_color=self.border, corner_radius=10)
        self.search_entry.pack(side="left", padx=4)
        self.search_var.trace_add("write", lambda *a: self.refresh_transactions())

        cat_opts = ["All"] + self.data.all_categories()
        self.cat_filter_combo = ctk.CTkComboBox(right_tb, width=130, values=cat_opts,
                                                variable=self.cat_filter,
                                                fg_color=self.input_bg, border_color=self.border,
                                                corner_radius=10,
                                                command=lambda v: self.refresh_transactions())
        self.cat_filter_combo.pack(side="left", padx=4)

        sort_opts = ["Date (newest)", "Date (oldest)", "Amount ↓", "Amount ↑", "Category"]
        self.sort_combo = ctk.CTkComboBox(right_tb, width=150, values=sort_opts,
                                          variable=self.sort_var,
                                          fg_color=self.input_bg, border_color=self.border,
                                          corner_radius=10,
                                          command=lambda v: self.refresh_transactions())
        self.sort_combo.pack(side="left", padx=4)

        ctk.CTkButton(right_tb, text="⬇ Import CSV", command=self.import_csv_dialog,
                      fg_color=self.card_light, text_color=self.text, hover_color=self.card,
                      border_width=1, border_color=self.border, corner_radius=10,
                      height=32, width=110).pack(side="left", padx=4)

        ctk.CTkButton(right_tb, text="⬆ Export CSV", command=self.export_csv,
                      fg_color=self.card_light, text_color=self.text, hover_color=self.card,
                      border_width=1, border_color=self.border, corner_radius=10,
                      height=32, width=110).pack(side="left", padx=4)

        if HAS_PDF:
            ctk.CTkButton(right_tb, text="📄 Export PDF", command=self.export_pdf,
                          fg_color=self.card_light, text_color=self.text, hover_color=self.card,
                          border_width=1, border_color=self.border, corner_radius=10,
                          height=32, width=110).pack(side="left", padx=4)

        ctk.CTkButton(right_tb, text="✕ Clear All", command=self.clear_all,
                      fg_color="transparent", text_color=self.danger, hover_color="#4A1A2A",
                      corner_radius=10, height=32, width=90).pack(side="left", padx=4)

        chip_row = ctk.CTkFrame(list_card, fg_color="transparent")
        chip_row.pack(fill="x", padx=18, pady=(0, 8))
        for f, lbl in [("all", "All"), ("income", "Income"), ("expense", "Expense")]:
            ctk.CTkRadioButton(chip_row, text=lbl, variable=self.filter_var, value=f,
                               command=self.refresh_transactions,
                               text_color=self.text_muted, fg_color=self.cyan,
                               font=(FONT_FAMILY, 12)).pack(side="left", padx=10)

        self._tx_summary = ctk.CTkLabel(list_card, text="", font=(FONT_FAMILY, 11),
                                         text_color=self.text_muted)
        self._tx_summary.pack(anchor="w", padx=18, pady=(0, 6))

        hdr = ctk.CTkFrame(list_card, fg_color=self.card_light, corner_radius=0)
        hdr.pack(fill="x", padx=18)
        for txt, w in [("Date", 110), ("Description", 0), ("Category", 150), ("Amount", 140), ("Notes", 160), ("", 90)]:
            kw = {"width": w} if w else {}
            ctk.CTkLabel(hdr, text=txt, font=(FONT_FAMILY, 11, "bold"),
                         text_color=self.text_muted, anchor="w", **kw).pack(side="left", padx=8, pady=6)

        self._tx_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent", corner_radius=0)
        self._tx_scroll.pack(fill="both", expand=True, padx=18, pady=(4, 14))

        self.refresh_transactions()

    def _build_add_form(self, parent):
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=18, pady=(4, 14))

        ctk.CTkLabel(form, text="Description", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).grid(row=0, column=0, sticky="w", padx=4, pady=(0, 2))
        ctk.CTkLabel(form, text="Amount", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(form, text="Type", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).grid(row=0, column=2, sticky="w", padx=4)
        ctk.CTkLabel(form, text="Category", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).grid(row=0, column=3, sticky="w", padx=4)
        ctk.CTkLabel(form, text="Date (YYYY-MM-DD)", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).grid(row=0, column=4, sticky="w", padx=4)
        ctk.CTkLabel(form, text="Notes (optional)", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).grid(row=0, column=5, sticky="w", padx=4)

        self.desc_entry = ctk.CTkEntry(form, width=220, placeholder_text="e.g. Coffee, Salary",
                                        fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self.desc_entry.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self.amount_entry = ctk.CTkEntry(form, width=120, placeholder_text="0.00",
                                          fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self.amount_entry.grid(row=1, column=1, padx=4, pady=4)

        self.trans_type = ctk.StringVar(value="expense")
        type_frame = ctk.CTkFrame(form, fg_color=self.input_bg, corner_radius=10,
                                   border_width=1, border_color=self.border)
        type_frame.grid(row=1, column=2, padx=4, pady=4)
        for val, lbl, color in [("expense", "Expense", self.danger), ("income", "Income", self.success)]:
            ctk.CTkRadioButton(type_frame, text=lbl, variable=self.trans_type, value=val,
                               fg_color=color, text_color=color,
                               font=(FONT_FAMILY, 12)).pack(side="left", padx=8, pady=6)

        self.cat_entry = ctk.CTkComboBox(form, width=150, values=self.data.all_categories(),
                                          fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self.cat_entry.set("")
        self.cat_entry.grid(row=1, column=3, padx=4, pady=4)

        today_str = datetime.now().strftime("%Y-%m-%d")
        self.date_entry = ctk.CTkEntry(form, width=140, placeholder_text=today_str,
                                        fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self.date_entry.insert(0, today_str)
        self.date_entry.grid(row=1, column=4, padx=4, pady=4)

        self.notes_entry = ctk.CTkEntry(form, width=180, placeholder_text="Optional note",
                                         fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self.notes_entry.grid(row=1, column=5, padx=4, pady=4)

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.grid(row=1, column=6, padx=4, pady=4)
        self._add_card_title_var = ctk.StringVar(value="+ Add (Ctrl+S)")
        self._add_btn = ctk.CTkButton(btn_frame, textvariable=self._add_card_title_var,
                                       command=self._submit_transaction,
                                       fg_color=self.cyan, text_color="#000000",
                                       font=(FONT_FAMILY, 12, "bold"), height=36, width=120,
                                       corner_radius=10)
        self._add_btn.pack(side="left", padx=2)
        self._cancel_btn = ctk.CTkButton(btn_frame, text="Cancel (Esc)", command=self._cancel_edit,
                                          fg_color=self.card_light, text_color=self.text_muted,
                                          height=36, width=100, corner_radius=10)

        for entry in [self.desc_entry, self.amount_entry, self.date_entry, self.notes_entry]:
            entry.bind("<Return>", lambda e: self._submit_transaction())

    # ── Filter state ──────────────────────────────────────────────────────────
    def _get_filtered_sorted(self):
        fv = self.filter_var.get(); cv = self.cat_filter.get(); sv = self.search_var.get().lower().strip()
        result = []
        for t in self.data.transactions:
            if fv == "income"  and t["amount"] <= 0: continue
            if fv == "expense" and t["amount"] >= 0: continue
            if cv != "All" and t.get("category") != cv: continue
            if sv and sv not in t["description"].lower(): continue
            result.append(t)
        mode = self.sort_var.get()
        if mode == "Date (newest)": result.sort(key=lambda x: x["id"], reverse=True)
        elif mode == "Date (oldest)": result.sort(key=lambda x: x["id"])
        elif mode == "Amount ↓": result.sort(key=lambda x: x["amount"], reverse=True)
        elif mode == "Amount ↑": result.sort(key=lambda x: x["amount"])
        elif mode == "Category": result.sort(key=lambda x: x.get("category", "").lower())
        return result

    def refresh_transactions(self):
        if not hasattr(self, "_tx_scroll"): return
        filtered = self._get_filtered_sorted()
        inc = sum(t["amount"] for t in filtered if t["amount"] > 0)
        exp = abs(sum(t["amount"] for t in filtered if t["amount"] < 0))
        self._tx_summary.configure(
            text=f"{len(filtered)} transactions   ↑ ₱{inc:,.2f}   ↓ ₱{exp:,.2f}   Net ₱{inc-exp:,.2f}"
        )
        for w in self._tx_scroll.winfo_children(): w.destroy()

        if not filtered:
            ctk.CTkLabel(self._tx_scroll, text="No transactions match your filters.",
                         font=(FONT_FAMILY, 13), text_color=self.text_muted).pack(pady=30)
            return

        for i, t in enumerate(filtered[:300]):
            bg = self.card if i % 2 == 0 else self.row_alt
            is_income = t["amount"] > 0
            amt_color = self.success if is_income else self.danger
            emoji = cat_emoji(t.get("category", ""))

            row = ctk.CTkFrame(self._tx_scroll, fg_color=bg, corner_radius=10)
            row.pack(fill="x", pady=1)

            date_str = datetime.fromisoformat(t["date"]).strftime("%b %d, %Y")
            ctk.CTkLabel(row, text=date_str, font=(FONT_FAMILY, 11),
                         text_color=self.text_muted, width=110, anchor="w"
                         ).pack(side="left", padx=8, pady=9)

            desc_frame = ctk.CTkFrame(row, fg_color="transparent")
            desc_frame.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(desc_frame, text=f"{emoji}  {t['description']}",
                         font=(FONT_FAMILY, 13), text_color=self.text, anchor="w"
                         ).pack(anchor="w", pady=8)

            cat = t.get("category", "")
            badge_bg = self.cat_color(cat)
            badge = ctk.CTkLabel(row, text=cat, font=(FONT_FAMILY, 10, "bold"),
                                  text_color="#000000", fg_color=badge_bg,
                                  corner_radius=8, width=120, height=24)
            badge.pack(side="left", padx=8)

            sign = "+" if is_income else "−"
            ctk.CTkLabel(row, text=f"{sign}₱{abs(t['amount']):,.2f}",
                         font=(FONT_FAMILY, 13, "bold"), text_color=amt_color,
                         width=140, anchor="w").pack(side="left", padx=8)

            notes = t.get("notes", "")
            ctk.CTkLabel(row, text=notes if notes else "—",
                         font=(FONT_FAMILY, 11), text_color=self.text_muted,
                         width=160, anchor="w").pack(side="left", padx=4)

            act = ctk.CTkFrame(row, fg_color="transparent", width=90)
            act.pack(side="left", padx=4)
            ctk.CTkButton(act, text="✏", width=32, height=28, fg_color="transparent",
                          text_color=self.cyan, hover_color=self.card_light, corner_radius=8,
                          command=lambda tid=t["id"]: self._start_edit(tid)
                          ).pack(side="left", padx=2)
            ctk.CTkButton(act, text="✕", width=32, height=28, fg_color="transparent",
                          text_color=self.danger, hover_color="#4A1A2A", corner_radius=8,
                          command=lambda tid=t["id"]: self._delete_txn(tid)
                          ).pack(side="left", padx=2)

        if len(filtered) > 300:
            ctk.CTkLabel(self._tx_scroll, text=f"Showing first 300 of {len(filtered)}.",
                         font=(FONT_FAMILY, 11), text_color=self.text_muted).pack(pady=8)

    # ── Transaction actions ──────────────────────────────────────────────────
    def _submit_transaction(self):
        desc   = self.desc_entry.get().strip()
        amt_s  = self.amount_entry.get().strip()
        cat    = self.cat_entry.get().strip()
        notes  = self.notes_entry.get().strip()
        date_s = self.date_entry.get().strip()

        if not desc or not amt_s or not cat:
            messagebox.showerror("Missing info", "Please fill Description, Amount and Category.")
            return
        try: amt = float(amt_s)
        except ValueError:
            messagebox.showerror("Invalid amount", "Amount must be a number."); return
        if amt <= 0:
            messagebox.showerror("Invalid amount", "Amount must be greater than zero."); return
        signed = abs(amt) if self.trans_type.get() == "income" else -abs(amt)

        try: date = datetime.strptime(date_s, "%Y-%m-%d") if date_s else datetime.now()
        except ValueError:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD format."); return

        if self.editing_txn_id is not None:
            self.data.update_transaction(self.editing_txn_id, desc, signed, cat, notes)
            self._cancel_edit()
        else:
            self.data.add_transaction(desc, signed, cat, date=date, notes=notes)
            self.desc_entry.delete(0, "end")
            self.amount_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            today = datetime.now().strftime("%Y-%m-%d")
            self.date_entry.delete(0, "end"); self.date_entry.insert(0, today)
            self.cat_entry.set("")

        self.refresh_all()
        self.status_lbl.configure(text=f"Saved transaction: {desc}")

    def _start_edit(self, txn_id):
        t = next((x for x in self.data.transactions if x["id"] == txn_id), None)
        if not t: return
        self.editing_txn_id = txn_id
        self.desc_entry.delete(0, "end"); self.desc_entry.insert(0, t["description"])
        self.amount_entry.delete(0, "end"); self.amount_entry.insert(0, f"{abs(t['amount']):.2f}")
        self.trans_type.set("income" if t["amount"] > 0 else "expense")
        self.cat_entry.set(t.get("category", ""))
        self.notes_entry.delete(0, "end"); self.notes_entry.insert(0, t.get("notes", ""))
        date_s = datetime.fromisoformat(t["date"]).strftime("%Y-%m-%d")
        self.date_entry.delete(0, "end"); self.date_entry.insert(0, date_s)
        self._add_card_title_var.set("💾 Save (Ctrl+S)")
        self._cancel_btn.pack(side="left", padx=2)

    def _cancel_edit(self):
        self.editing_txn_id = None
        for entry in [self.desc_entry, self.amount_entry, self.notes_entry]:
            entry.delete(0, "end")
        self.cat_entry.set(""); self.trans_type.set("expense")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._add_card_title_var.set("+ Add (Ctrl+S)")
        self._cancel_btn.pack_forget()

    def _delete_txn(self, txn_id):
        t = next((x for x in self.data.transactions if x["id"] == txn_id), None)
        if t and messagebox.askyesno("Delete", f"Delete '{t['description']}'?"):
            self.data.delete_transaction(txn_id)
            if self.editing_txn_id == txn_id: self._cancel_edit()
            self.refresh_all()
            self.status_lbl.configure(text=f"Deleted: {t['description']}")

    def clear_all(self):
        if messagebox.askyesno("Clear All", "Delete ALL transactions? This cannot be undone."):
            self.data.clear_transactions()
            self.refresh_all()
            self.status_lbl.configure(text="All transactions cleared.")

    def export_csv(self):
        if not self.data.transactions:
            messagebox.showinfo("Export", "No transactions to export."); return
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not fp: return
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Description", "Category", "Amount", "Type", "Notes"])
            for t in self.data.transactions:
                date = datetime.fromisoformat(t["date"]).strftime("%Y-%m-%d")
                typ = "Income" if t["amount"] > 0 else "Expense"
                w.writerow([date, t["description"], t["category"], abs(t["amount"]), typ, t.get("notes", "")])
        messagebox.showinfo("Exported", f"Saved to {fp}")
        self.status_lbl.configure(text=f"Exported CSV: {fp}")

    def export_pdf(self):
        if not HAS_PDF:
            messagebox.showinfo("PDF Export", "ReportLab not installed. Please install it with: pip install reportlab")
            return
        if not self.data.transactions:
            messagebox.showinfo("Export", "No transactions to export."); return
        fp = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not fp: return
        try:
            c = canvas.Canvas(fp, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, height - 50, "Tribby Financial Report")
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 80, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            c.setFont("Helvetica", 10)
            y = height - 120
            for t in self.data.transactions[:50]:
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 10)
                line = f"{datetime.fromisoformat(t['date']).strftime('%Y-%m-%d')}  {t['description']}  ₱{abs(t['amount']):,.2f}  {t.get('category','')}"
                c.drawString(50, y, line[:100])
                y -= 20
            c.save()
            messagebox.showinfo("Exported", f"PDF saved to {fp}")
            self.status_lbl.configure(text=f"Exported PDF: {fp}")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

    def import_csv_dialog(self):
        fp = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not fp: return
        added, skipped = self.data.import_csv(fp)
        self.refresh_all()
        self.status_lbl.configure(text=f"Imported {added} rows, skipped {skipped}")
        messagebox.showinfo("Import Complete", f"Imported {added} transactions. Skipped {skipped} rows.")

    # =========================================================================
    # BUDGET & GOALS  (unchanged from previous)
    # =========================================================================
    def show_budget_goals(self):
        self.current_view = "budget"
        self._set_nav("budget")
        self._clear_content()
        self._page_header(self.content, "Budget & Goals", "Plan your spending · track your savings")

        outer = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(outer, fg_color=self.card, corner_radius=18,
                            border_width=1, border_color=self.border)
        left.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="nsew")
        card_title(left, self, "Monthly Budget", "Your overall spending limit", "◎")

        disp_frame = ctk.CTkFrame(left, fg_color="transparent")
        disp_frame.pack(fill="x", padx=18, pady=(6, 0))
        self._budget_lbl = ctk.CTkLabel(disp_frame, text=f"₱{self.data.budget:,.2f}",
                                         font=(FONT_FAMILY, 30, "bold"), text_color=self.cyan)
        self._budget_lbl.pack(side="left")
        ctk.CTkLabel(disp_frame, text="/ month", font=(FONT_FAMILY, 12),
                     text_color=self.text_muted).pack(side="left", padx=8, pady=4)

        qs = ctk.CTkFrame(left, fg_color="transparent")
        qs.pack(fill="x", padx=18, pady=8)
        ctk.CTkLabel(qs, text="Quick set:", font=(FONT_FAMILY, 11),
                     text_color=self.text_muted).pack(side="left", padx=(0, 8))
        for amt in [10000, 15000, 20000, 30000, 50000]:
            ctk.CTkButton(qs, text=f"₱{amt:,}", width=76, height=30, fg_color=self.card_light,
                          text_color=self.text, hover_color=self.border, corner_radius=8,
                          border_width=1, border_color=self.border,
                          command=lambda a=amt: self._set_budget(a)).pack(side="left", padx=3)

        ce = ctk.CTkFrame(left, fg_color="transparent")
        ce.pack(fill="x", padx=18, pady=(0, 8))
        self._budget_entry = ctk.CTkEntry(ce, width=140, placeholder_text="Custom amount",
                                           fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._budget_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(ce, text="Set", width=60, height=32, fg_color=self.cyan,
                      text_color="#000000", corner_radius=10,
                      command=self._set_budget_custom).pack(side="left")

        self._budget_slider = ctk.CTkSlider(left, from_=1000, to=200000, number_of_steps=199,
                                             command=self._set_budget, button_color=self.cyan,
                                             progress_color=self.cyan, button_hover_color=self.purple)
        self._budget_slider.pack(fill="x", padx=18, pady=(4, 10))
        self._budget_slider.set(self.data.budget)

        self._budget_prog = ctk.CTkProgressBar(left, height=10, corner_radius=99)
        self._budget_prog.pack(fill="x", padx=18, pady=(0, 4))
        self._budget_stats_lbl = ctk.CTkLabel(left, text="", font=(FONT_FAMILY, 11),
                                               text_color=self.text_muted)
        self._budget_stats_lbl.pack(pady=(0, 12))

        section_sep(left, self)
        card_title(left, self, "Category Budgets", "Monthly limits per category", "☰")

        cf = ctk.CTkFrame(left, fg_color="transparent")
        cf.pack(fill="x", padx=18, pady=(4, 8))
        self._cat_budget_combo = ctk.CTkComboBox(cf, width=150, values=self.data.all_categories(),
                                                  fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._cat_budget_combo.pack(side="left", padx=(0, 8))
        self._cat_budget_entry = ctk.CTkEntry(cf, width=110, placeholder_text="Limit amount",
                                               fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._cat_budget_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(cf, text="Set", width=60, height=32, fg_color=self.purple,
                      text_color="#FFFFFF", corner_radius=10,
                      command=self._set_cat_budget).pack(side="left")

        self._cat_budgets_container = ctk.CTkScrollableFrame(left, fg_color="transparent", height=260)
        self._cat_budgets_container.pack(fill="x", padx=16, pady=(0, 14))

        right = ctk.CTkFrame(outer, fg_color=self.card, corner_radius=18,
                             border_width=1, border_color=self.border)
        right.grid(row=0, column=1, padx=(8, 0), pady=4, sticky="nsew")
        card_title(right, self, "Savings Goals", "Track your financial targets", "↑")

        gf = ctk.CTkFrame(right, fg_color="transparent")
        gf.pack(fill="x", padx=18, pady=(4, 10))
        self._goal_name = ctk.CTkEntry(gf, width=180, placeholder_text="Goal name",
                                         fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._goal_name.pack(side="left", padx=(0, 8))
        self._goal_target = ctk.CTkEntry(gf, width=130, placeholder_text="Target ₱",
                                           fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._goal_target.pack(side="left", padx=(0, 8))
        self._goal_date = ctk.CTkEntry(gf, width=130, placeholder_text="Target date (opt.)",
                                         fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._goal_date.pack(side="left", padx=(0, 8))
        ctk.CTkButton(gf, text="+ Create", width=90, height=32, fg_color=self.purple,
                      text_color="#FFFFFF", corner_radius=10,
                      command=self._add_goal).pack(side="left")

        self._goals_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._goals_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self._refresh_budget_ui()
        self._refresh_cat_budgets()
        self._refresh_goals()

    def _set_budget(self, value):
        v = int(float(value))
        if v < 1000: return
        self.data.budget = v; self.data.save_budget()
        self._refresh_budget_ui()
        self._update_stats()

    def _set_budget_custom(self):
        try:
            v = float(self._budget_entry.get().strip())
            if v < 1000: raise ValueError
            self._set_budget(v)
            self._budget_entry.delete(0, "end")
        except ValueError:
            messagebox.showerror("Error", "Enter an amount of at least ₱1,000.")

    def _refresh_budget_ui(self):
        if not hasattr(self, "_budget_lbl"): return
        b = self.data.budget
        self._budget_lbl.configure(text=f"₱{b:,.2f}")
        self._budget_slider.set(b)
        spent = self.data.total_expenses()
        usage = spent / b if b > 0 else 0
        color = self.danger if usage >= 1.0 else (self.warning if usage >= 0.8 else self.success)
        self._budget_prog.configure(progress_color=color)
        self._budget_prog.set(min(usage, 1.0))
        remain = b - spent
        self._budget_stats_lbl.configure(
            text=f"Spent ₱{spent:,.2f}   |   {'Remaining' if remain >= 0 else 'Over by'} ₱{abs(remain):,.2f}"
        )

    def _set_cat_budget(self):
        cat = self._cat_budget_combo.get().strip()
        s = self._cat_budget_entry.get().strip()
        if not cat: messagebox.showerror("Error", "Select a category."); return
        try:
            amt = float(s)
            if amt <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a positive amount."); return
        self.data.set_category_budget(cat, amt)
        self._cat_budget_entry.delete(0, "end")
        self._refresh_cat_budgets()

    def _refresh_cat_budgets(self):
        if not hasattr(self, "_cat_budgets_container"): return
        for w in self._cat_budgets_container.winfo_children(): w.destroy()
        if not self.data.category_budgets:
            ctk.CTkLabel(self._cat_budgets_container, text="No category limits set yet.",
                         font=(FONT_FAMILY, 12), text_color=self.text_muted).pack(pady=12)
            return
        spent = self.data.spending_by_category_this_month()
        for cat, limit in self.data.category_budgets.items():
            s = spent.get(cat, 0)
            usage = min(s / limit, 1.0) if limit > 0 else 0
            color = self.danger if usage >= 1.0 else (self.warning if usage >= 0.8 else self.success)

            row = ctk.CTkFrame(self._cat_budgets_container, fg_color=self.card_light,
                               corner_radius=12, border_width=1, border_color=self.border)
            row.pack(fill="x", pady=4)
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))
            badge_color = self.cat_color(cat)
            ctk.CTkLabel(top, text=f"{cat_emoji(cat)}  {cat}", font=(FONT_FAMILY, 12, "bold"),
                         text_color=self.text).pack(side="left")
            ctk.CTkLabel(top, text=f"₱{s:,.0f} / ₱{limit:,.0f}",
                         font=(FONT_FAMILY, 11), text_color=color).pack(side="left", padx=10)
            ctk.CTkButton(top, text="✕", width=26, height=26, fg_color="transparent",
                          text_color=self.danger, hover_color="#4A1A2A",
                          corner_radius=6, command=lambda c=cat: self._del_cat_budget(c)
                          ).pack(side="right")
            pb = ctk.CTkProgressBar(row, height=7, corner_radius=99, progress_color=color)
            pb.pack(fill="x", padx=12, pady=(2, 10))
            pb.set(usage)

    def _del_cat_budget(self, cat):
        self.data.set_category_budget(cat, 0)
        self._refresh_cat_budgets()

    def _add_goal(self):
        name = self._goal_name.get().strip()
        tstr = self._goal_target.get().strip()
        dstr = self._goal_date.get().strip() or None
        if not name or not tstr:
            messagebox.showerror("Error", "Enter a goal name and target amount."); return
        try:
            target = float(tstr)
            if target <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive target amount."); return
        self.data.add_goal(name, target, target_date=dstr)
        self._goal_name.delete(0, "end"); self._goal_target.delete(0, "end"); self._goal_date.delete(0, "end")
        self._refresh_goals()
        self._update_stats()

    def _refresh_goals(self):
        if not hasattr(self, "_goals_scroll"): return
        for w in self._goals_scroll.winfo_children(): w.destroy()
        if not self.data.goals:
            ctk.CTkLabel(self._goals_scroll, text="✨  No goals yet. Create one above!",
                         font=(FONT_FAMILY, 13), text_color=self.text_muted).pack(pady=30)
            return
        for g in self.data.goals:
            pct = (g["current"] / g["target"] * 100) if g["target"] > 0 else 0
            done = pct >= 100
            bar_color = self.success if done else self.cyan

            card = ctk.CTkFrame(self._goals_scroll, fg_color=self.card_light, corner_radius=14,
                                border_width=1,
                                border_color=self.success if done else self.border)
            card.pack(fill="x", pady=5)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=14, pady=(10, 2))
            name_text = f"🎉  {g['name']}" if done else f"◎  {g['name']}"
            ctk.CTkLabel(hdr, text=name_text, font=(FONT_FAMILY, 13, "bold"),
                         text_color=self.success if done else self.cyan).pack(side="left")
            ctk.CTkLabel(hdr, text=f"{pct:.0f}%", font=(FONT_FAMILY, 12, "bold"),
                         text_color=bar_color).pack(side="left", padx=8)

            if g.get("target_date"):
                ctk.CTkLabel(hdr, text=f"🗓  {g['target_date']}", font=(FONT_FAMILY, 10),
                             text_color=self.text_muted).pack(side="left", padx=4)

            ctk.CTkButton(hdr, text="✕", width=26, height=26, fg_color="transparent",
                          text_color=self.danger, hover_color="#4A1A2A", corner_radius=6,
                          command=lambda gid=g["id"]: self._del_goal(gid)).pack(side="right")

            ctk.CTkLabel(card, text=f"₱{g['current']:,.2f} saved  /  ₱{g['target']:,.2f} target",
                         font=(FONT_FAMILY, 11), text_color=self.text_muted).pack(anchor="w", padx=14)

            pb = ctk.CTkProgressBar(card, height=8, corner_radius=99, progress_color=bar_color)
            pb.pack(fill="x", padx=14, pady=(4, 8))
            pb.set(min(pct / 100, 1.0))

            if not done:
                dep_row = ctk.CTkFrame(card, fg_color="transparent")
                dep_row.pack(fill="x", padx=14, pady=(0, 10))
                ctk.CTkLabel(dep_row, text="Add:", font=(FONT_FAMILY, 10),
                             text_color=self.text_muted).pack(side="left", padx=(0, 6))
                for amt in [50, 100, 500, 1000]:
                    ctk.CTkButton(dep_row, text=f"+₱{amt}", width=62, height=26,
                                  fg_color=self.card, border_width=1, border_color=self.border,
                                  text_color=self.text, hover_color=self.card_light,
                                  corner_radius=8, font=(FONT_FAMILY, 10),
                                  command=lambda a=amt, gid=g["id"]: self._deposit_goal(gid, a)
                                  ).pack(side="left", padx=3)
                custom = ctk.CTkEntry(dep_row, width=90, placeholder_text="Custom",
                                      fg_color=self.input_bg, border_color=self.border, corner_radius=8,
                                      font=(FONT_FAMILY, 10))
                custom.pack(side="left", padx=6)
                ctk.CTkButton(dep_row, text="Add", width=50, height=26,
                              fg_color=self.purple, text_color="#FFFFFF", corner_radius=8,
                              font=(FONT_FAMILY, 10),
                              command=lambda gid=g["id"], e=custom: self._deposit_custom(gid, e)
                              ).pack(side="left")

    def _deposit_goal(self, gid, amount):
        self.data.update_goal(gid, amount)
        self._refresh_goals()
        self._update_stats()
        self.status_lbl.configure(text=f"Added ₱{amount} to goal")

    def _deposit_custom(self, gid, entry):
        try:
            amt = float(entry.get().strip())
            if amt <= 0: raise ValueError
            self.data.update_goal(gid, amt)
            entry.delete(0, "end")
            self._refresh_goals()
            self._update_stats()
            self.status_lbl.configure(text=f"Added ₱{amt} to goal")
        except ValueError:
            messagebox.showerror("Error", "Enter a positive amount.")

    def _del_goal(self, gid):
        if messagebox.askyesno("Delete Goal", "Permanently delete this goal?"):
            self.data.delete_goal(gid)
            self._refresh_goals()
            self._update_stats()
            self.status_lbl.configure(text="Goal deleted")

    # =========================================================================
    # RECURRING  (unchanged)
    # =========================================================================
    def show_recurring(self):
        self.current_view = "recurring"
        self._set_nav("recurring")
        self._clear_content()
        self._page_header(self.content, "Recurring Transactions",
                          "Automate bills, subscriptions and regular income")

        add_card = make_card(self.content, self, pady=(0, 10))
        card_title(add_card, self, "New Recurring Item", None, "↻")

        form = ctk.CTkFrame(add_card, fg_color="transparent")
        form.pack(fill="x", padx=18, pady=(4, 14))

        for col, (lbl, w) in enumerate([
            ("Description", 220), ("Amount", 120),
            ("Type", 160), ("Category", 150), ("Repeats", 120)
        ]):
            ctk.CTkLabel(form, text=lbl, font=(FONT_FAMILY, 11), text_color=self.text_muted,
                         ).grid(row=0, column=col, sticky="w", padx=4, pady=(0, 2))

        self._rec_desc = ctk.CTkEntry(form, width=220, placeholder_text="e.g. Rent, Netflix",
                                       fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._rec_desc.grid(row=1, column=0, padx=4, pady=4)

        self._rec_amt = ctk.CTkEntry(form, width=120, placeholder_text="0.00",
                                      fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._rec_amt.grid(row=1, column=1, padx=4, pady=4)

        self._rec_type = ctk.StringVar(value="expense")
        tf = ctk.CTkFrame(form, fg_color=self.input_bg, corner_radius=10,
                          border_width=1, border_color=self.border)
        tf.grid(row=1, column=2, padx=4, pady=4)
        for val, lbl, color in [("expense", "Expense", self.danger), ("income", "Income", self.success)]:
            ctk.CTkRadioButton(tf, text=lbl, variable=self._rec_type, value=val,
                               fg_color=color, text_color=color,
                               font=(FONT_FAMILY, 12)).pack(side="left", padx=8, pady=6)

        self._rec_cat = ctk.CTkComboBox(form, width=150, values=self.data.all_categories(),
                                         fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._rec_cat.set(""); self._rec_cat.grid(row=1, column=3, padx=4, pady=4)

        self._rec_interval = ctk.CTkComboBox(form, width=120, values=RECUR_INTERVALS,
                                              fg_color=self.input_bg, border_color=self.border, corner_radius=10)
        self._rec_interval.set("Monthly")
        self._rec_interval.grid(row=1, column=4, padx=4, pady=4)

        ctk.CTkButton(form, text="+ Add Recurring", command=self._add_recurring,
                      fg_color=self.cyan, text_color="#000000", font=(FONT_FAMILY, 12, "bold"),
                      height=36, corner_radius=10).grid(row=1, column=5, padx=10, pady=4, sticky="w")

        rec_items = self.data.recurring
        monthly_cost = sum(
            (abs(r["amount"]) * (30 if r["interval"]=="Daily" else
                                  4.33 if r["interval"]=="Weekly" else
                                  1 if r["interval"]=="Monthly" else
                                  1/12))
            for r in rec_items
        )
        strip = ctk.CTkFrame(self.content, fg_color=self.card_light, corner_radius=12,
                             border_width=1, border_color=self.border)
        strip.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(strip,
                     text=f"↻  {len(rec_items)} recurring item{'s' if len(rec_items)!=1 else ''}   |   "
                          f"Est. monthly cost: ₱{monthly_cost:,.2f}",
                     font=(FONT_FAMILY, 12), text_color=self.text_muted).pack(pady=8, padx=18, anchor="w")

        list_card = ctk.CTkFrame(self.content, fg_color=self.card, corner_radius=18,
                                 border_width=1, border_color=self.border)
        list_card.pack(fill="both", expand=True, pady=(0, 16))
        card_title(list_card, self, "Active Items", None, "↻")

        self._rec_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._rec_scroll.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        self._refresh_recurring()

    def _add_recurring(self):
        desc = self._rec_desc.get().strip()
        amts = self._rec_amt.get().strip()
        cat = self._rec_cat.get().strip()
        intv = self._rec_interval.get()
        if not desc or not amts or not cat:
            messagebox.showerror("Missing info", "Fill Description, Amount and Category."); return
        try:
            amt = float(amts)
            if amt <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Enter a positive amount."); return
        signed = abs(amt) if self._rec_type.get() == "income" else -abs(amt)
        self.data.add_recurring(desc, signed, cat, intv, datetime.now())
        self._rec_desc.delete(0, "end"); self._rec_amt.delete(0, "end"); self._rec_cat.set("")
        self._refresh_recurring()
        self.status_lbl.configure(text=f"Added recurring: {desc}")

    def _refresh_recurring(self):
        if not hasattr(self, "_rec_scroll"): return
        for w in self._rec_scroll.winfo_children(): w.destroy()
        if not self.data.recurring:
            ctk.CTkLabel(self._rec_scroll, text="✨  No recurring items yet. Add one above!",
                         font=(FONT_FAMILY, 13), text_color=self.text_muted).pack(pady=30)
            return
        now = datetime.now()
        items = sorted(self.data.recurring, key=lambda r: r["next_date"])
        for r in items:
            is_income = r["amount"] > 0
            amt_color = self.success if is_income else self.danger
            sign = "+" if is_income else "−"
            next_dt   = datetime.fromisoformat(r["next_date"])
            days_until= (next_dt.date() - now.date()).days

            if days_until < 0:   due_lbl = "Overdue";  due_color = self.danger
            elif days_until == 0: due_lbl = "Due today"; due_color = self.warning
            elif days_until <= 3: due_lbl = f"In {days_until}d"; due_color = self.warning
            else:                 due_lbl = next_dt.strftime("%b %d, %Y"); due_color = self.text_muted

            row = ctk.CTkFrame(self._rec_scroll, fg_color=self.card_light, corner_radius=14,
                               border_width=1, border_color=self.border)
            row.pack(fill="x", pady=4)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=14, pady=10)

            top = ctk.CTkFrame(left, fg_color="transparent")
            top.pack(fill="x")
            ctk.CTkLabel(top, text=f"{cat_emoji(r['category'])}  {r['description']}",
                         font=(FONT_FAMILY, 13, "bold"), text_color=self.text).pack(side="left")

            badge_bg = self.cat_color(r["category"])
            ctk.CTkLabel(top, text=r["category"], font=(FONT_FAMILY, 9, "bold"),
                         text_color="#000000", fg_color=badge_bg, corner_radius=6,
                         width=80, height=20).pack(side="left", padx=10)

            meta = ctk.CTkFrame(left, fg_color="transparent")
            meta.pack(fill="x", pady=(3, 0))
            ctk.CTkLabel(meta, text=f"↻  {r['interval']}",
                         font=(FONT_FAMILY, 10), text_color=self.text_muted).pack(side="left")
            ctk.CTkLabel(meta, text=f"  |  🗓  {due_lbl}",
                         font=(FONT_FAMILY, 10), text_color=due_color).pack(side="left")

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=14, pady=10)
            ctk.CTkLabel(right, text=f"{sign}₱{abs(r['amount']):,.2f}",
                         font=(FONT_FAMILY, 14, "bold"), text_color=amt_color).pack(anchor="e")
            ctk.CTkButton(right, text="✕ Remove", width=90, height=26,
                          fg_color="transparent", text_color=self.danger,
                          hover_color="#4A1A2A", corner_radius=8, font=(FONT_FAMILY, 10),
                          command=lambda rid=r["id"]: self._del_recurring(rid)).pack(anchor="e", pady=(4, 0))

    def _del_recurring(self, rid):
        if messagebox.askyesno("Remove", "Remove this recurring item? Past transactions stay."):
            self.data.delete_recurring(rid)
            self._refresh_recurring()
            self.status_lbl.configure(text="Recurring item removed")

    # =========================================================================
    # Global refresh
    # =========================================================================
    def refresh_all(self):
        self._update_stats()
        if self.current_view == "dashboard":
            self._update_dashboard()
        elif self.current_view == "transactions":
            self.refresh_transactions()
        elif self.current_view == "budget":
            self._refresh_budget_ui()
            self._refresh_cat_budgets()
            self._refresh_goals()
        elif self.current_view == "recurring":
            self._refresh_recurring()


# ── Helper widgets ──────────────────────────────────────────────────────────

def make_card(parent, app, padx=0, pady=0, corner=18, expand=False, fill="x"):
    f = ctk.CTkFrame(parent, fg_color=app.card, corner_radius=corner,
                     border_width=1, border_color=app.border)
    f.pack(fill=fill, expand=expand, padx=padx, pady=pady)
    return f

def card_title(parent, app, title, subtitle=None, icon=None):
    hdr = ctk.CTkFrame(parent, fg_color="transparent")
    hdr.pack(fill="x", padx=18, pady=(14, 2))
    lbl_text = f"{icon}  {title}" if icon else title
    ctk.CTkLabel(hdr, text=lbl_text,
                 font=(FONT_FAMILY, 14, "bold"), text_color=app.cyan).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(hdr, text=subtitle,
                     font=(FONT_FAMILY, 11), text_color=app.text_muted).pack(anchor="w")

def section_sep(parent, app):
    ctk.CTkFrame(parent, height=1, fg_color=app.border).pack(fill="x", padx=18, pady=6)


# ── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TribbyApp()
    app.mainloop()