# Expense Tracker

**Expense Tracker** is a CS50x final project for recording, managing, searching, and analyzing personal expenses.

## Features

- User registration, login, and logout
- Case-sensitive usernames using letters, numbers, and underscores
- Live username and email availability checks
- Password show/hide controls
- Add, view, edit, and delete expenses
- Predefined expense categories
- Search and filtering by description, category, date range, and amount
- Dashboard with spending totals, expense count, averages, category chart, and spending-over-time chart
- Password reset using email OTP verification
- Account page with password change
- Account deletion with email OTP verification and final confirmation
- Minimal deleted-account record for username, email, and deletion timestamp
- Reusable site footer across all pages
- Bootstrap-based responsive UI

## Technology

- Python
- Flask
- SQLite / SQL
- HTML / CSS / JavaScript
- Bootstrap
- Jinja
- Chart.js

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```text
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your own secret key and email settings.
4. Initialize the SQLite database:

```text
python database.py
```

5. Start the application:

```text
python app.py
```

6. Open the local Flask address shown in the terminal.

## Security note

`.env` and `database.db` are intentionally excluded from the project repository/archive. Do not commit real credentials or personal database data.

## Current known issue

Deleted-account recreation is intentionally paused for later fixing. The existing eight-character minimum password requirement remains unchanged.
