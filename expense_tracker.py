"""Personal Expense Tracker - Tkinter + SQLite academic prototype."""
import csv
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

DB_FILE = Path(__file__).with_name("expenses.db")
CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Education",
              "Entertainment", "Health", "Other"]
PAYMENT_MODES = ["Cash", "UPI", "Card", "Net Banking"]
COLUMNS = ["id", "title", "amount", "category", "exp_date", "payment_mode", "notes"]


# ---------------------------- database layer ----------------------------
def connect():
    return sqlite3.connect(DB_FILE)


def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, amount REAL NOT NULL,
            category TEXT NOT NULL, exp_date TEXT NOT NULL,
            payment_mode TEXT NOT NULL, notes TEXT)""")


def validate(d):
    """Return an error message, or None if the data is acceptable."""
    if not d["title"].strip():
        return "Title is required."
    try:
        if float(d["amount"]) <= 0:
            raise ValueError
    except ValueError:
        return "Amount must be a number greater than 0."
    try:
        datetime.strptime(d["exp_date"], "%Y-%m-%d")
    except ValueError:
        return "Date must be in YYYY-MM-DD format."
    if d["category"] not in CATEGORIES or d["payment_mode"] not in PAYMENT_MODES:
        return "Please choose a valid category and payment mode."
    return None


def add_expense(d):
    with connect() as con:
        con.execute("INSERT INTO expenses(title,amount,category,exp_date,payment_mode,notes)"
                    " VALUES(?,?,?,?,?,?)",
                    (d["title"], float(d["amount"]), d["category"], d["exp_date"],
                     d["payment_mode"], d["notes"]))


def update_expense(rec_id, d):
    with connect() as con:
        con.execute("UPDATE expenses SET title=?,amount=?,category=?,exp_date=?,"
                    "payment_mode=?,notes=? WHERE id=?",
                    (d["title"], float(d["amount"]), d["category"], d["exp_date"],
                     d["payment_mode"], d["notes"], rec_id))


def delete_expense(rec_id):
    with connect() as con:
        con.execute("DELETE FROM expenses WHERE id=?", (rec_id,))


def fetch(search="", category="All", month=""):
    sql, args = "SELECT * FROM expenses WHERE 1=1", []
    if search:
        sql += " AND (title LIKE ? OR notes LIKE ?)"
        args += [f"%{search}%"] * 2
    if category != "All":
        sql += " AND category=?"
        args.append(category)
    if month:
        sql += " AND exp_date LIKE ?"
        args.append(f"{month}%")
    with connect() as con:
        return con.execute(sql + " ORDER BY exp_date DESC, id DESC", args).fetchall()


def category_totals():
    with connect() as con:
        return con.execute("SELECT category, COUNT(*), SUM(amount) FROM expenses "
                           "GROUP BY category ORDER BY SUM(amount) DESC").fetchall()


def stats():
    """Return (total spent, this month's spend, transaction count, top category)."""
    month = datetime.now().strftime("%Y-%m")
    with connect() as con:
        total = con.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        this_month = con.execute("SELECT COALESCE(SUM(amount),0) FROM expenses "
                                 "WHERE exp_date LIKE ?", (f"{month}%",)).fetchone()[0]
        count = con.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    totals = category_totals()
    return total, this_month, count, (totals[0][0] if totals else "-")


# --------------------------------- GUI ---------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Expense Tracker")
        self.geometry("1000x620")
        self.selected_id = None
        self.vars = {k: tk.StringVar() for k in COLUMNS[1:]}
        self.vars["exp_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.search_var = tk.StringVar()
        self.cat_filter = tk.StringVar(value="All")
        self.month_var = tk.StringVar()
        self.build_dashboard()
        self.build_form()
        self.build_table()
        self.refresh()

    def build_dashboard(self):
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="x")
        self.cards = {}
        for name in ("Total Spent", "This Month", "Transactions", "Top Category"):
            box = ttk.LabelFrame(frame, text=name, padding=8)
            box.pack(side="left", expand=True, fill="x", padx=4)
            self.cards[name] = ttk.Label(box, text="0", font=("Arial", 16, "bold"))
            self.cards[name].pack()

    def build_form(self):
        frame = ttk.LabelFrame(self, text="Expense Details", padding=8)
        frame.pack(fill="x", padx=10, pady=4)
        labels = [("Title", "title"), ("Amount (Rs.)", "amount"),
                  ("Category", "category"), ("Date (YYYY-MM-DD)", "exp_date"),
                  ("Payment mode", "payment_mode"), ("Notes", "notes")]
        choices = {"category": CATEGORIES, "payment_mode": PAYMENT_MODES}
        for i, (text, key) in enumerate(labels):
            r, c = divmod(i, 3)
            ttk.Label(frame, text=text).grid(row=r, column=c * 2, sticky="w", padx=4, pady=3)
            if key in choices:
                w = ttk.Combobox(frame, textvariable=self.vars[key],
                                 values=choices[key], state="readonly", width=20)
            else:
                w = ttk.Entry(frame, textvariable=self.vars[key], width=23)
            w.grid(row=r, column=c * 2 + 1, padx=4, pady=3)
        bar = ttk.Frame(frame)
        bar.grid(row=2, column=0, columnspan=6, pady=6)
        for text, cmd in [("Add", self.on_add), ("Update", self.on_update),
                          ("Delete", self.on_delete), ("Clear", self.clear_form),
                          ("Category Summary", self.show_summary),
                          ("Export CSV", self.on_export)]:
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=4)

    def build_table(self):
        top = ttk.Frame(self, padding=(10, 0))
        top.pack(fill="x")
        ttk.Label(top, text="Search:").pack(side="left")
        ttk.Entry(top, textvariable=self.search_var, width=22).pack(side="left", padx=4)
        ttk.Label(top, text="Category:").pack(side="left")
        ttk.Combobox(top, textvariable=self.cat_filter, values=["All"] + CATEGORIES,
                     state="readonly", width=14).pack(side="left", padx=4)
        ttk.Label(top, text="Month (YYYY-MM):").pack(side="left")
        ttk.Entry(top, textvariable=self.month_var, width=9).pack(side="left", padx=4)
        ttk.Button(top, text="Apply", command=self.refresh).pack(side="left", padx=4)
        ttk.Button(top, text="Reset", command=self.reset_filters).pack(side="left")
        self.tree = ttk.Treeview(self, columns=COLUMNS, show="headings", height=10)
        for col in COLUMNS:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=40 if col == "id" else 130, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ----- actions -----
    def form_data(self):
        return {k: v.get().strip() for k, v in self.vars.items()}

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for row in fetch(self.search_var.get().strip(), self.cat_filter.get(),
                         self.month_var.get().strip()):
            self.tree.insert("", "end", values=row)
        total, month, count, top = stats()
        self.cards["Total Spent"].config(text=f"Rs. {total:,.2f}")
        self.cards["This Month"].config(text=f"Rs. {month:,.2f}")
        self.cards["Transactions"].config(text=str(count))
        self.cards["Top Category"].config(text=top)

    def reset_filters(self):
        self.search_var.set("")
        self.cat_filter.set("All")
        self.month_var.set("")
        self.refresh()

    def clear_form(self):
        for k, v in self.vars.items():
            v.set(datetime.now().strftime("%Y-%m-%d") if k == "exp_date" else "")
        self.selected_id = None

    def on_add(self):
        d = self.form_data()
        error = validate(d)
        if error:
            return messagebox.showerror("Invalid input", error)
        add_expense(d)
        self.clear_form()
        self.refresh()

    def on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            values = self.tree.item(sel[0])["values"]
            self.selected_id = values[0]
            for key, val in zip(COLUMNS[1:], values[1:]):
                self.vars[key].set(str(val))

    def on_update(self):
        if not self.selected_id:
            return messagebox.showwarning("Select record", "Select an expense first.")
        d = self.form_data()
        error = validate(d)
        if error:
            return messagebox.showerror("Invalid input", error)
        update_expense(self.selected_id, d)
        self.clear_form()
        self.refresh()

    def on_delete(self):
        if not self.selected_id:
            return messagebox.showwarning("Select record", "Select an expense first.")
        if messagebox.askyesno("Confirm", "Delete the selected expense?"):
            delete_expense(self.selected_id)
            self.clear_form()
            self.refresh()

    def show_summary(self):
        win = tk.Toplevel(self)
        win.title("Category Summary")
        tree = ttk.Treeview(win, columns=("c", "n", "t"), show="headings", height=9)
        for col, text in zip(("c", "n", "t"), ("Category", "Transactions", "Total (Rs.)")):
            tree.heading(col, text=text)
            tree.column(col, width=130, anchor="center")
        for cat, n, total in category_totals():
            tree.insert("", "end", values=(cat, n, f"{total:,.2f}"))
        tree.pack(padx=10, pady=10)

    def on_export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)
                writer.writerows(fetch())
            messagebox.showinfo("Exported", f"Records exported to:\n{path}")


if __name__ == "__main__":
    init_db()
    App().mainloop()
