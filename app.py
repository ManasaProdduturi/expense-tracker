from flask import Flask, render_template, request
from database import get_db_connection

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

        print(username, email, password, confirm_password)

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)