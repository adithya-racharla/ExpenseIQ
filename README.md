# ExpenseIQ — Intermediate Expense Tracker

A full-stack expense tracking web application built with Python, Flask, and SQLite.

---

## Tech Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite (via Python's built-in `sqlite3`)
- **Frontend**: Jinja2 templates, Chart.js, vanilla CSS
- **Export**: CSV generation via Python's `csv` module

---

## Features

- ✅ Add, edit, delete expenses
- ✅ Category management (add custom categories)
- ✅ Filter by category and month
- ✅ Sort by date or amount
- ✅ Dashboard with summary cards
- ✅ Interactive charts (monthly trend + category breakdown)
- ✅ Monthly & category-wise summary page
- ✅ Export all data to CSV
- ✅ Form validation with flash messages
- ✅ Responsive dark UI

---

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
# http://127.0.0.1:5000
```

---

## Project Structure

```
expense_tracker/
├── app.py                  # Flask routes + SQLite logic
├── requirements.txt
├── expenses.db             # Auto-created on first run
└── templates/
    ├── base.html           # Shared layout + sidebar
    ├── index.html          # Dashboard
    ├── expenses.html       # All expenses (filter/edit/delete)
    └── summary.html        # Analytics & monthly breakdown
```

---

## Resume Bullet Points

- Built a full-stack expense tracker using **Python & Flask** with a responsive web interface
- Designed and queried a **SQLite relational database** with full CRUD operations using raw SQL
- Implemented **dynamic filtering, sorting, and category-wise analytics** across all expense records
- Integrated **Chart.js** for interactive data visualizations (trend lines, doughnut charts, bar charts)
- Added **CSV export** functionality using Python's built-in `csv` module
- Deployed-ready with clean MVC-style separation of concerns

---

## Deployment (Free)

**Render.com:**
1. Push to GitHub
2. Create a new Web Service on Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add `gunicorn` to requirements.txt

Then paste your live URL on your resume!
