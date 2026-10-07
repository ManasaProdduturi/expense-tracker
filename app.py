from flask import Flask, render_template, request
from database import get_db_connection
from werkzeug.security import generate_password_hash

app = Flask(__name__)


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

        print(username, email, password_hash)

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)