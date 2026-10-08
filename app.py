from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from datetime import date
import sqlite3
import os
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def login_required():
    if "user_id" not in session:
        return redirect(url_for("login"))


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    connection = get_db_connection()

    if request.method == "POST":
        amount = request.form["amount"].strip()
        expense_date = request.form["date"].strip()
        category_id = request.form["category_id"].strip()
        description = request.form["description"].strip()

        # Validate amount
        try:
            amount = float(amount)

            if amount <= 0:
                raise ValueError

        except ValueError:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "add_expense.html",
                categories=categories,
                today=date.today().isoformat(),
                error="Amount must be a positive number."
            )

        # Validate date
        try:
            expense_date_obj = date.fromisoformat(expense_date)

        except ValueError:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "add_expense.html",
                categories=categories,
                today=date.today().isoformat(),
                error="Please enter a valid date."
            )

        if expense_date_obj > date.today():
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "add_expense.html",
                categories=categories,
                today=date.today().isoformat(),
                error="Expense date cannot be in the future."
            )

        # Validate category
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()

        if category is None:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "add_expense.html",
                categories=categories,
                today=date.today().isoformat(),
                error="Please select a valid category."
            )

        # Validate description length
        if len(description) > 500:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "add_expense.html",
                categories=categories,
                today=date.today().isoformat(),
                error="Description must be 500 characters or less."
            )

        connection.execute(
            """
            INSERT INTO expenses
            (user_id, category_id, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                category_id,
                amount,
                expense_date,
                description
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("expenses"))

    categories = connection.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()

    connection.close()

    return render_template(
        "add_expense.html",
        categories=categories,
        today=date.today().isoformat()
    )


@app.route("/expenses")
def expenses():
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    min_amount = request.args.get("min_amount", "").strip()
    max_amount = request.args.get("max_amount", "").strip()

    connection = get_db_connection()

    # Validate category
    if category:
        category_exists = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category,)
        ).fetchone()

        if category_exists is None:
            connection.close()
            return "Invalid category."

    # Validate dates
    try:
        if date_from:
            date.fromisoformat(date_from)

        if date_to:
            date.fromisoformat(date_to)
    except ValueError:
        connection.close()
        return "Invalid date."

    if date_from and date_to and date_from > date_to:
        connection.close()
        return "From date cannot be after To date."

    # Validate minimum amount
    if min_amount:
        try:
            min_amount_value = float(min_amount)

            if min_amount_value < 0:
                raise ValueError

        except ValueError:
            connection.close()
            return "Minimum amount must be a valid non-negative number."

    # Validate maximum amount
    if max_amount:
        try:
            max_amount_value = float(max_amount)

            if max_amount_value < 0:
                raise ValueError

        except ValueError:
            connection.close()
            return "Maximum amount must be a valid non-negative number."

    # Validate amount range
    if min_amount and max_amount:
        if float(min_amount) > float(max_amount):
            connection.close()
            return "Minimum amount cannot be greater than maximum amount."

    # Limit search length
    if len(search) > 100:
        connection.close()
        return "Search text is too long."

    expenses = connection.execute(
        """
        SELECT
            expenses.*,
            categories.name AS category_name
        FROM expenses
        JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
          AND expenses.description LIKE ?
          AND (? = '' OR expenses.category_id = ?)
          AND (? = '' OR expenses.date >= ?)
          AND (? = '' OR expenses.date <= ?)
          AND (? = '' OR expenses.amount >= ?)
          AND (? = '' OR expenses.amount <= ?)
        ORDER BY expenses.date DESC
        """,
        (
            session["user_id"],
            f"%{search}%",
            category,
            category,
            date_from,
            date_from,
            date_to,
            date_to,
            min_amount,
            min_amount,
            max_amount,
            max_amount
        )
    ).fetchall()

    categories = connection.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()

    connection.close()

    return render_template(
    "expenses.html",
    expenses=expenses,
    search=search,
    categories=categories,
    selected_category=category,
    date_from=date_from,
    date_to=date_to,
    min_amount=min_amount,
    max_amount=max_amount,
    today=date.today().isoformat()
)


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    connection = get_db_connection()

    expense = connection.execute(
        """
        SELECT *
        FROM expenses
        WHERE id = ? AND user_id = ?
        """,
        (expense_id, session["user_id"])
    ).fetchone()

    if expense is None:
        connection.close()
        return "Expense not found!"

    if request.method == "POST":
        amount = request.form["amount"].strip()
        expense_date = request.form["date"].strip()
        category_id = request.form["category_id"].strip()
        description = request.form["description"].strip()

        # Validate amount
        try:
            amount = float(amount)

            if amount <= 0:
                raise ValueError

        except ValueError:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=categories,
                today=date.today().isoformat(),
                error="Amount must be a positive number."
            )

        # Validate date
        try:
            expense_date_obj = date.fromisoformat(expense_date)

        except ValueError:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=categories,
                today=date.today().isoformat(),
                error="Please enter a valid date."
            )

        if expense_date_obj > date.today():
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=categories,
                today=date.today().isoformat(),
                error="Expense date cannot be in the future."
            )

        # Validate category
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()

        if category is None:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=categories,
                today=date.today().isoformat(),
                error="Please select a valid category."
            )

        # Validate description length
        if len(description) > 500:
            categories = connection.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()

            connection.close()

            return render_template(
                "edit_expense.html",
                expense=expense,
                categories=categories,
                today=date.today().isoformat(),
                error="Description must be 500 characters or less."
            )

        connection.execute(
            """
            UPDATE expenses
            SET amount = ?, date = ?, category_id = ?, description = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                amount,
                expense_date,
                category_id,
                description,
                expense_id,
                session["user_id"]
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("expenses"))

    categories = connection.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()

    connection.close()

    return render_template(
        "edit_expense.html",
        expense=expense,
        categories=categories,
        today=date.today().isoformat()
    )


@app.route("/expenses/<int:expense_id>/delete")
def delete_expense(expense_id):
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM expenses
        WHERE id = ? AND user_id = ?
        """,
        (expense_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    return redirect(url_for("expenses"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        connection = get_db_connection()

        # Check username first
        existing_username = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_username:
            connection.close()

            return render_template(
                "register.html",
                error="Username already exists.",
                username=username,
                email=email
            )

        # Check email second
        existing_email = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:
            connection.close()

            return render_template(
                "register.html",
                error="Email already exists.",
                username=username,
                email=email
            )

        connection.close()

        # Validate password after account checks
        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must be at least 8 characters long.",
                username=username,
                email=email
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match.",
                username=username,
                email=email
            )

        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (username, email, password_hash)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            return render_template(
                "login.html",
                error="Username and password are required."
            )

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        # Account does not exist
        if user is None:
            return render_template(
                "login.html",
                error="Account does not exist."
            )

        # Incorrect password
        if not check_password_hash(
            user["password_hash"],
            password
        ):
            return render_template(
                "login.html",
                error="Incorrect password."
            )

        session.clear()
        session["user_id"] = user["id"]

        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/categories")
def categories():
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    connection = get_db_connection()

    categories = connection.execute(
        "SELECT * FROM categories ORDER BY name"
    ).fetchall()

    connection.close()

    return render_template(
        "categories.html",
        categories=categories
    )


@app.route("/dashboard")
def dashboard():
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    period = request.args.get("period", "all")

    connection = get_db_connection()

    total_spending = connection.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total_spending
        FROM expenses
        WHERE user_id = ?
        AND (
            ? = 'all'
            OR (? = 'month' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now'))
            OR (? = 'last_month' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now', '-1 month'))
            OR (? = 'year' AND strftime('%Y', date) = strftime('%Y', 'now'))
        )
        """,
        (
            session["user_id"],
            period,
            period,
            period,
            period
        )
    ).fetchone()["total_spending"]

    expense_count = connection.execute(
        """
        SELECT COUNT(*) AS expense_count
        FROM expenses
        WHERE user_id = ?
        AND (
            ? = 'all'
            OR (? = 'month' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now'))
            OR (? = 'last_month' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now', '-1 month'))
            OR (? = 'year' AND strftime('%Y', date) = strftime('%Y', 'now'))
        )
        """,
        (
            session["user_id"],
            period,
            period,
            period,
            period
        )
    ).fetchone()["expense_count"]

    category_spending = connection.execute(
        """
        SELECT
            categories.name AS category_name,
            SUM(expenses.amount) AS total_amount
        FROM expenses
        JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        AND (
            ? = 'all'
            OR (? = 'month' AND strftime('%Y-%m', expenses.date) = strftime('%Y-%m', 'now'))
            OR (? = 'last_month' AND strftime('%Y-%m', expenses.date) = strftime('%Y-%m', 'now', '-1 month'))
            OR (? = 'year' AND strftime('%Y', expenses.date) = strftime('%Y', 'now'))
        )
        GROUP BY expenses.category_id
        ORDER BY total_amount DESC
        """,
        (
            session["user_id"],
            period,
            period,
            period,
            period
        )
    ).fetchall()

    category_spending = [
    {
        "category_name": category["category_name"],
        "total_amount": category["total_amount"]
    }
    for category in category_spending
    ]

    recent_expenses = connection.execute(
        """
        SELECT
            expenses.*,
            categories.name AS category_name
        FROM expenses
        JOIN categories
            ON expenses.category_id = categories.id
        WHERE expenses.user_id = ?
        AND (
            ? = 'all'
            OR (? = 'month' AND strftime('%Y-%m', expenses.date) = strftime('%Y-%m', 'now'))
            OR (? = 'last_month' AND strftime('%Y-%m', expenses.date) = strftime('%Y-%m', 'now', '-1 month'))
            OR (? = 'year' AND strftime('%Y', expenses.date) = strftime('%Y', 'now'))
        )
        ORDER BY expenses.date DESC
        LIMIT 5
        """,
        (
            session["user_id"],
            period,
            period,
            period,
            period
        )
    ).fetchall()

    spending_over_time = connection.execute(
        """
        SELECT
            date,
            SUM(amount) AS total_amount
        FROM expenses
        WHERE user_id = ?
        AND (
            ? = 'all'
            OR (? = 'month' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now'))
            OR (? = 'last_month' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now', '-1 month'))
            OR (? = 'year' AND strftime('%Y', date) = strftime('%Y', 'now'))
        )
        GROUP BY date
        ORDER BY date
        """,
        (
            session["user_id"],
            period,
            period,
            period,
            period
        )
    ).fetchall()

    spending_over_time = [
    {
        "date": spending["date"],
        "total_amount": spending["total_amount"]
    }
    for spending in spending_over_time
]

    connection.close()

    return render_template(
        "dashboard.html",
        total_spending=total_spending,
        expense_count=expense_count,
        category_spending=category_spending,
        recent_expenses=recent_expenses,
        spending_over_time=spending_over_time,
        period=period
    )


@app.route("/check-username")
def check_username():
    username = request.args.get("username", "").strip()

    if not username:
        return jsonify({"available": False, "message": ""})

    connection = get_db_connection()

    user = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()

    if user:
        return jsonify({
            "available": False,
            "message": "Username is already taken."
        })

    return jsonify({
        "available": True,
        "message": "Username is available."
    })


@app.route("/check-email")
def check_email():
    email = request.args.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "available": False,
            "message": ""
        })

    connection = get_db_connection()

    user = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    connection.close()

    if user:
        return jsonify({
            "available": False,
            "message": "Email is already registered."
        })

    return jsonify({
        "available": True,
        "message": "Email is available."
    })


if __name__ == "__main__":
    app.run(debug=True)