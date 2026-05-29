import csv
import io
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "expense_tracker_secret_key"

import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    default_categories = ["Food", "Transport", "Utilities", "Entertainment", "Health", "Shopping", "Others"]
    for cat in default_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    total = conn.execute("SELECT COALESCE(SUM(amount), 0) as total FROM expenses").fetchone()["total"]
    this_month = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) as total FROM expenses
        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """).fetchone()["total"]
    count = conn.execute("SELECT COUNT(*) as cnt FROM expenses").fetchone()["cnt"]
    top_category = conn.execute("""
        SELECT c.name, SUM(e.amount) as total
        FROM expenses e JOIN categories c ON e.category_id = c.id
        GROUP BY c.name ORDER BY total DESC LIMIT 1
    """).fetchone()
    recent = conn.execute("""
        SELECT e.id, e.date, c.name as category, e.description, e.amount
        FROM expenses e JOIN categories c ON e.category_id = c.id
        ORDER BY e.date DESC, e.created_at DESC LIMIT 10
    """).fetchall()
    breakdown = conn.execute("""
        SELECT c.name, SUM(e.amount) as total
        FROM expenses e JOIN categories c ON e.category_id = c.id
        GROUP BY c.name ORDER BY total DESC
    """).fetchall()
    trend = conn.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM expenses GROUP BY month ORDER BY month DESC LIMIT 6
    """).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()

    return render_template("index.html",
        total=total,
        this_month=this_month,
        count=count,
        top_category=top_category,
        recent=[dict(r) for r in recent],
        breakdown=[{"name": r["name"], "total": r["total"]} for r in breakdown],
        trend=[{"month": r["month"], "total": r["total"]} for r in list(reversed(trend))],
        categories=[dict(r) for r in categories],
        today=date.today().isoformat()
    )

@app.route("/add", methods=["POST"])
def add_expense():
    exp_date = request.form.get("date")
    category_id = request.form.get("category_id")
    description = request.form.get("description", "").strip()
    amount = request.form.get("amount")

    errors = []
    if not exp_date:
        errors.append("Date is required.")
    if not category_id:
        errors.append("Category is required.")
    if not description:
        errors.append("Description is required.")
    try:
        amount = float(amount)
        if amount <= 0:
            errors.append("Amount must be positive.")
    except (ValueError, TypeError):
        errors.append("Invalid amount.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (date, category_id, description, amount) VALUES (?, ?, ?, ?)",
        (exp_date, category_id, description, amount)
    )
    conn.commit()
    conn.close()
    flash("Expense added successfully!", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    flash("Expense deleted.", "info")
    return redirect(url_for("index"))

@app.route("/expenses")
def all_expenses():
    category_filter = request.args.get("category", "")
    month_filter = request.args.get("month", "")
    sort_by = request.args.get("sort", "date_desc")

    order_map = {
        "date_desc": "e.date DESC, e.created_at DESC",
        "date_asc": "e.date ASC",
        "amount_desc": "e.amount DESC",
        "amount_asc": "e.amount ASC",
    }
    order_clause = order_map.get(sort_by, "e.date DESC")

    query = """
        SELECT e.id, e.date, c.name as category, c.id as category_id,
               e.description, e.amount
        FROM expenses e JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    params = []
    if category_filter:
        query += " AND c.name = ?"
        params.append(category_filter)
    if month_filter:
        query += " AND strftime('%Y-%m', e.date) = ?"
        params.append(month_filter)
    query += f" ORDER BY {order_clause}"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    expenses = []
    for r in rows:
        d = dict(r)
        d["description_safe"] = d["description"].replace("'", " ")
        expenses.append(d)

    categories = [dict(r) for r in conn.execute("SELECT * FROM categories ORDER BY name").fetchall()]
    total = sum(e["amount"] for e in expenses)

    available_months = [r["month"] for r in conn.execute("""
        SELECT DISTINCT strftime('%Y-%m', date) as month
        FROM expenses ORDER BY month DESC
    """).fetchall()]

    conn.close()

    return render_template("expenses.html",
        expenses=expenses,
        categories=categories,
        category_filter=category_filter,
        month_filter=month_filter,
        sort_by=sort_by,
        total=total,
        available_months=available_months
    )

@app.route("/edit/<int:expense_id>", methods=["POST"])
def edit_expense(expense_id):
    exp_date = request.form.get("date")
    category_id = request.form.get("category_id")
    description = request.form.get("description", "").strip()
    amount = request.form.get("amount")

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        flash("Invalid amount.", "error")
        return redirect(url_for("all_expenses"))

    conn = get_db()
    conn.execute(
        "UPDATE expenses SET date=?, category_id=?, description=?, amount=? WHERE id=?",
        (exp_date, category_id, description, amount, expense_id)
    )
    conn.commit()
    conn.close()
    flash("Expense updated!", "success")
    return redirect(url_for("all_expenses"))

@app.route("/add_category", methods=["POST"])
def add_category():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Category name cannot be empty.", "error")
        return redirect(url_for("index"))
    conn = get_db()
    try:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        flash(f'Category "{name}" added!', "success")
    except sqlite3.IntegrityError:
        flash(f'Category "{name}" already exists.', "error")
    conn.close()
    return redirect(url_for("index"))

@app.route("/summary")
def summary():
    conn = get_db()
    monthly = [dict(r) for r in conn.execute("""
        SELECT strftime('%Y-%m', date) as month,
               SUM(amount) as total, COUNT(*) as cnt
        FROM expenses GROUP BY month ORDER BY month DESC
    """).fetchall()]
    by_category = [dict(r) for r in conn.execute("""
        SELECT c.name, SUM(e.amount) as total, COUNT(*) as cnt,
               AVG(e.amount) as avg
        FROM expenses e JOIN categories c ON e.category_id = c.id
        GROUP BY c.name ORDER BY total DESC
    """).fetchall()]
    conn.close()
    return render_template("summary.html", monthly=monthly, by_category=by_category)

@app.route("/export")
def export_csv():
    conn = get_db()
    expenses = conn.execute("""
        SELECT e.date, c.name as category, e.description, e.amount
        FROM expenses e JOIN categories c ON e.category_id = c.id
        ORDER BY e.date DESC
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Description", "Amount"])
    for e in expenses:
        writer.writerow([e["date"], e["category"], e["description"], e["amount"]])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
