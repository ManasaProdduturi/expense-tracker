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
            return "Username or email already exists!"

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

        return "Login successful!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return "Logged out successfully!"


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

    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)