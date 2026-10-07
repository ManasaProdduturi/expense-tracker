from flask import Flask, render_template, request, session, redirect, url_for
from datetime import date
import sqlite3
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"


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
        amount = request.form["amount"]
        expense_date = request.form["date"]
        category_id = request.form["category_id"]
        description = request.form["description"]

        # Prevent future dates
        if expense_date > date.today().isoformat():
            connection.close()
            return "Expense date cannot be in the future!"

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
        "SELECT * FROM categories"
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

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    min_amount = request.args.get("min_amount", "")
    max_amount = request.args.get("max_amount", "")

    connection = get_db_connection()

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
    max_amount=max_amount
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
        amount = request.form["amount"]
        expense_date = request.form["date"]
        category_id = request.form["category_id"]
        description = request.form["description"]

        # Prevent future dates
        if expense_date > date.today().isoformat():
            connection.close()
            return "Expense date cannot be in the future!"

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
        "SELECT * FROM categories"
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
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, email, password_hash)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return render_template(
                "register.html",
                error="That username or email is already registered. Please try another one."
            )

        connection.close()

        return "Registration successful!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        connection.close()

        if user is None:
            return "Invalid username or password!"

        if not check_password_hash(user["password_hash"], password):
            return "Invalid username or password!"

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


if __name__ == "__main__":
    app.run(debug=True)