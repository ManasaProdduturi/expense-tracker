from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key"

def login_required():
    if "user_id" not in session:
        return redirect(url_for("login"))

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


@app.route("/profile")
def profile():
    redirect_response = login_required()

    if redirect_response:
        return redirect_response

    return f"Logged in as user ID: {session['user_id']}"


@app.route("/logout")
def logout():
    session.clear()
    return "Logged out successfully!"


if __name__ == "__main__":
    app.run(debug=True)