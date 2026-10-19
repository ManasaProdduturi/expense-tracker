from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash

from datetime import date, datetime, timedelta

import os

from database import get_db_connection, initialize_database

from werkzeug.security import generate_password_hash, check_password_hash

import re

import secrets

import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv

import math

from flask import send_from_directory

from pathlib import Path





load_dotenv()





app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]



initialize_database()



CURRENCY_SYMBOLS = {

    "INR": "₹",

    "USD": "$",

    "GBP": "£",

    "EUR": "€",

    "JPY": "¥",

    "KRW": "₩",

    "AUD": "$",

    "CAD": "$",

}



@app.context_processor

def inject_currency_symbol():

    currency = session.get("currency", "INR")

    return {

        "currency_symbol": CURRENCY_SYMBOLS.get(

            currency, CURRENCY_SYMBOLS["INR"]

        )

    }



def login_required():



    if "user_id" not in session:



        return redirect(url_for("login"))





def send_otp_email(recipient_email, otp):



    message = EmailMessage()





    message["Subject"] = "Expense Tracker - Password Reset OTP"



    message["From"] = os.environ.get("EMAIL_FROM")



    message["To"] = recipient_email





    message.set_content(



        f"""Hello,







We received a request to reset your Expense Tracker password.







Your password reset OTP is:







{otp}







This OTP will expire in 10 minutes.







If you did not request a password reset, you can safely ignore this email.







Regards,



Expense Tracker



"""



    )







    smtp_host = os.environ.get("SMTP_HOST")



    smtp_port = int(os.environ.get("SMTP_PORT", 465))



    smtp_username = os.environ.get("SMTP_USERNAME")



    smtp_password = os.environ.get("SMTP_PASSWORD")







    with smtplib.SMTP_SSL(



        smtp_host,



        smtp_port,



        timeout=30



    ) as server:







        server.login(



            smtp_username,



            smtp_password



        )







        server.send_message(message)







def send_account_deletion_otp_email(email, otp):

    message = EmailMessage()

    message["Subject"] = "Expense Tracker - Account Deletion Verification"

    message["From"] = os.environ.get("EMAIL_FROM")

    message["To"] = email



    message.set_content(

        f"""Hello,



We received a request to delete your Expense Tracker account.



Your account deletion verification code is:



{otp}



This code will expire in 10 minutes.



If you did not request account deletion, you can safely ignore this email.



Regards,

Expense Tracker

"""

    )



    smtp_host = os.environ.get("SMTP_HOST")

    smtp_port = int(os.environ.get("SMTP_PORT", 465))

    smtp_username = os.environ.get("SMTP_USERNAME")

    smtp_password = os.environ.get("SMTP_PASSWORD")



    with smtplib.SMTP_SSL(

        smtp_host,

        smtp_port,

        timeout=30

    ) as server:

        server.login(

            smtp_username,

            smtp_password

        )

        server.send_message(message)





def send_account_deleted_email(email, username):

    message = EmailMessage()

    message["Subject"] = "Expense Tracker - Account Deleted"

    message["From"] = os.environ.get("EMAIL_FROM")

    message["To"] = email



    message.set_content(

        f"""Hello {username},



Your Expense Tracker account has been permanently deleted.



Your expenses and account data have been removed.



This is the final email you will receive from Expense Tracker.



Regards,

Expense Tracker

"""

    )



    smtp_host = os.environ.get("SMTP_HOST")

    smtp_port = int(os.environ.get("SMTP_PORT", 465))

    smtp_username = os.environ.get("SMTP_USERNAME")

    smtp_password = os.environ.get("SMTP_PASSWORD")



    with smtplib.SMTP_SSL(

        smtp_host,

        smtp_port,

        timeout=30

    ) as server:

        server.login(

            smtp_username,

            smtp_password

        )

        server.send_message(message)









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





            if not math.isfinite(max_amount_value) or not 0 <= max_amount_value <= 10000000:

                raise ValueError







        except ValueError:



            connection.close()



            return "Maximum amount must be between 0 and 10,000,000."







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







@app.route("/expenses/add", methods=["GET", "POST"])

def add_expense():

    redirect_response = login_required()

    if redirect_response:

        return redirect_response



    connection = get_db_connection()



    def render_add_form(error=None):

        categories = connection.execute(

            "SELECT * FROM categories ORDER BY name"

        ).fetchall()



        return render_template(

            "expense_form.html",

            categories=categories,

            today=date.today().isoformat(),

            error=error,

            is_edit=False,

        )



    if request.method == "POST":

        amount = request.form.get("amount", "").strip()

        expense_date = request.form.get("date", "").strip()

        category_id = request.form.get("category_id", "").strip()

        description = request.form.get("description", "").strip()



        try:

            amount = float(amount)

            if not math.isfinite(amount) or amount <= 0 or amount > 10000000:

                raise ValueError

        except ValueError:

            response = render_add_form(

                "Amount must be greater than 0 and cannot exceed 10,000,000."

            )

            connection.close()

            return response



        try:

            expense_date_obj = date.fromisoformat(expense_date)

        except ValueError:

            response = render_add_form("Please enter a valid date.")

            connection.close()

            return response



        if expense_date_obj > date.today():

            response = render_add_form("Expense date cannot be in the future.")

            connection.close()

            return response



        category = connection.execute(

            "SELECT id FROM categories WHERE id = ?",

            (category_id,),

        ).fetchone()



        if category is None:

            response = render_add_form("Please select a valid category.")

            connection.close()

            return response



        if len(description) > 500:

            response = render_add_form(

                "Description must be 500 characters or less."

            )

            connection.close()

            return response



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

                description,

            ),

        )



        connection.commit()

        connection.close()

        return redirect(url_for("expenses"))



    response = render_add_form()

    connection.close()

    return response





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

        (expense_id, session["user_id"]),

    ).fetchone()



    if expense is None:

        connection.close()

        return "Expense not found!", 404



    def render_edit_form(error=None):

        categories = connection.execute(

            "SELECT * FROM categories ORDER BY name"

        ).fetchall()



        return render_template(

            "expense_form.html",

            expense=expense,

            categories=categories,

            today=date.today().isoformat(),

            error=error,

            is_edit=True,

        )



    if request.method == "POST":

        amount = request.form.get("amount", "").strip()

        expense_date = request.form.get("date", "").strip()

        category_id = request.form.get("category_id", "").strip()

        description = request.form.get("description", "").strip()



        try:

            amount = float(amount)

            if not math.isfinite(amount) or amount <= 0:

                raise ValueError

        except ValueError:

            response = render_edit_form("Amount must be a positive number.")

            connection.close()

            return response



        try:

            expense_date_obj = date.fromisoformat(expense_date)

        except ValueError:

            response = render_edit_form("Please enter a valid date.")

            connection.close()

            return response



        if expense_date_obj > date.today():

            response = render_edit_form("Expense date cannot be in the future.")

            connection.close()

            return response



        category = connection.execute(

            "SELECT id FROM categories WHERE id = ?",

            (category_id,),

        ).fetchone()



        if category is None:

            response = render_edit_form("Please select a valid category.")

            connection.close()

            return response



        if len(description) > 500:

            response = render_edit_form(

                "Description must be 500 characters or less."

            )

            connection.close()

            return response



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

                session["user_id"],

            ),

        )



        connection.commit()

        connection.close()

        return redirect(url_for("expenses"))



    response = render_edit_form()

    connection.close()

    return response











@app.route("/expenses/<int:expense_id>/delete", methods=["POST"])



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
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    currency = request.form.get("currency", "INR")

    errors = []

    # Username validation
    username_valid = bool(re.fullmatch(r"[A-Za-z0-9_]{3,30}", username))

    if not username:
        errors.append("Username is required.")
    elif not username_valid:
        errors.append(
            "Username must be 3–30 characters and contain only "
            "letters, numbers, and underscores."
        )

    # Email validation
    email_valid = bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))

    if not email:
        errors.append("Email address is required.")
    elif not email_valid:
        errors.append("Please enter a valid email address.")

    # Password validation
    if not password:
        errors.append("Password is required.")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    elif len(password) > 128:
        errors.append("Password must not exceed 128 characters.")

    # Password confirmation
    if not confirm_password:
        errors.append("Please confirm your password.")
    elif password != confirm_password:
        errors.append("Passwords do not match.")

    valid_currencies = {
        "INR", "USD", "GBP", "EUR",
        "JPY", "KRW", "AUD", "CAD"
    }

    if currency not in valid_currencies:
        errors.append("Invalid currency selected.")

    connection = get_db_connection()

    try:
        # Check both account fields so both duplicate errors can be shown.
        if username_valid:
            existing_username = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing_username:
                errors.append("Username already exists.")

        if email_valid:
            existing_email = connection.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if existing_email:
                errors.append("Email already exists.")

        if errors:
            return render_template(
                "register.html",
                errors=errors,
                username="",
                email="",
                currency=currency if currency in valid_currencies else "INR"
            )

        password_hash = generate_password_hash(password)

        connection.execute(
            """
            INSERT INTO users (username, email, password_hash, currency)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, currency)
        )

        # Preserve deleted-account history when the same email registers again.
        deleted_record = connection.execute(
            """
            SELECT id
            FROM deleted_users
            WHERE email = ? AND recreated = 0
            ORDER BY deleted_at DESC, id DESC
            LIMIT 1
            """,
            (email,)
        ).fetchone()

        if deleted_record:
            connection.execute(
                """
                UPDATE deleted_users
                SET recreated = 1, recreated_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), deleted_record["id"])
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])



def login():



    if request.method == "POST":



        username_or_email = request.form["username_or_email"].strip()



        password = request.form["password"]







        connection = get_db_connection()







        user = connection.execute(



            """



            SELECT *



            FROM users



            WHERE username = ? OR email = ?



            """,



            (username_or_email, username_or_email.lower())



        ).fetchone()







        connection.close()







        if not user or not check_password_hash(



            user["password_hash"],



            password



        ):



            return render_template(



                "login.html",



                error="Invalid username/email or password."



            )





        session.clear()

        session["user_id"] = user["id"]

        session["currency"] = user["currency"]





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



    if period not in ("all", "month", "last_month", "year"):

        return redirect(url_for("dashboard"))





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











@app.route("/account")



def account():



    redirect_response = login_required()







    if redirect_response:



        return redirect_response







    connection = get_db_connection()







    user = connection.execute(



        """



        SELECT username, email, currency



        FROM users



        WHERE id = ?



        """,



        (session["user_id"],)



    ).fetchone()







    connection.close()







    if user is None:



        session.clear()



        return redirect(url_for("login"))







    return render_template(



        "account.html",



        user=user



    )





@app.route("/account/change-currency", methods=["POST"])

def change_currency():

    redirect_response = login_required()

    if redirect_response:

        return redirect_response



    valid_currencies = {

        "INR", "USD", "GBP", "EUR",

        "JPY", "KRW", "AUD", "CAD"

    }



    currency = request.form.get("currency", "")



    if currency not in valid_currencies:

        flash("Invalid currency selected.", "danger")

        return redirect(url_for("account"))



    connection = get_db_connection()

    connection.execute(

        "UPDATE users SET currency = ? WHERE id = ?",

        (currency, session["user_id"])

    )

    connection.commit()

    connection.close()



    session["currency"] = currency

    flash("Currency updated successfully.", "success")

    return redirect(url_for("account"))





@app.route("/account/change-password", methods=["POST"])



def change_password():



    redirect_response = login_required()







    if redirect_response:



        return redirect_response







    current_password = request.form["current_password"]



    new_password = request.form["new_password"]



    confirm_password = request.form["confirm_password"]







    connection = get_db_connection()







    user = connection.execute(

    """

    SELECT username, email, password_hash

    FROM users

    WHERE id = ?

    """,

    (session["user_id"],)

    ).fetchone()







    if user is None:



        connection.close()



        session.clear()



        return redirect(url_for("login"))







    if not check_password_hash(



        user["password_hash"],



        current_password



    ):



        connection.close()







        return render_template(



            "account.html",



            user=user,



            error="Current password is incorrect."



        )







    if len(new_password) < 8:



        connection.close()







        return render_template(



            "account.html",



            user=user,



            error="New password must be at least 8 characters long."



        )







    if new_password != confirm_password:



        connection.close()







        return render_template(



            "account.html",



            user=user,



            error="New passwords do not match."



        )







    new_password_hash = generate_password_hash(new_password)







    connection.execute(



        """



        UPDATE users



        SET password_hash = ?



        WHERE id = ?



        """,



        (new_password_hash, session["user_id"])



    )







    connection.commit()



    connection.close()







    return redirect(url_for("account"))











@app.route("/account/delete-request", methods=["POST"])



def delete_account_request():



    redirect_response = login_required()







    if redirect_response:



        return redirect_response







    connection = get_db_connection()







    user = connection.execute(



        """



        SELECT id, email



        FROM users



        WHERE id = ?



        """,



        (session["user_id"],)



    ).fetchone()







    connection.close()







    if user is None:



        session.clear()



        return redirect(url_for("login"))







    otp = str(secrets.randbelow(900000) + 100000)



    otp_hash = generate_password_hash(otp)



    expires_at = datetime.now() + timedelta(minutes=10)







    connection = get_db_connection()







    connection.execute(



        """



        DELETE FROM account_delete_otps



        WHERE user_id = ?



        """,



        (user["id"],)



    )







    connection.execute(



        """



        INSERT INTO account_delete_otps



        (user_id, otp_hash, expires_at)



        VALUES (?, ?, ?)



        """,



        (



            user["id"],



            otp_hash,



            expires_at.isoformat()



        )



    )







    connection.commit()



    connection.close()







    try:



        send_account_deletion_otp_email(user["email"], otp)



    except Exception:



        connection = get_db_connection()







        connection.execute(



            """



            DELETE FROM account_delete_otps



            WHERE user_id = ?



            """,



            (user["id"],)



        )







        connection.commit()



        connection.close()







        return render_template(



            "account.html",



            user=user,



            error="Unable to send verification email. Please try again."



        )







    return redirect(



        url_for(



            "delete_account_verify",



            email=user["email"]



        )



    )











@app.route("/account/delete-verify", methods=["GET", "POST"])



def delete_account_verify():



    redirect_response = login_required()







    if redirect_response:



        return redirect_response







    if request.method == "POST":



        otp = request.form["otp"].strip()







        connection = get_db_connection()







        otp_record = connection.execute(



            """



            SELECT id, otp_hash, expires_at



            FROM account_delete_otps



            WHERE user_id = ?



            """,



            (session["user_id"],)



        ).fetchone()







        if otp_record is None:



            connection.close()







            return render_template(



                "delete_account_verify.html",



                error="Verification code is invalid or has expired."



            )







        expires_at = datetime.fromisoformat(otp_record["expires_at"])







        if datetime.now() > expires_at:



            connection.execute(



                """



                DELETE FROM account_delete_otps



                WHERE id = ?



                """,



                (otp_record["id"],)



            )







            connection.commit()



            connection.close()







            return render_template(



                "delete_account_verify.html",



                error="Verification code has expired."



            )







        if not check_password_hash(



            otp_record["otp_hash"],



            otp



        ):



            connection.close()







            return render_template(



                "delete_account_verify.html",



                error="Invalid verification code."



            )







        connection.execute(



            """



            DELETE FROM account_delete_otps



            WHERE id = ?



            """,



            (otp_record["id"],)



        )







        connection.commit()



        connection.close()







        session["delete_verified"] = True







        return redirect(url_for("delete_account_confirm"))







    connection = get_db_connection()







    user = connection.execute(



        """



        SELECT email



        FROM users



        WHERE id = ?



        """,



        (session["user_id"],)



    ).fetchone()







    connection.close()







    if user is None:



        session.clear()



        return redirect(url_for("login"))







    return render_template(



        "delete_account_verify.html",



        email=user["email"]



    )











@app.route("/account/delete-confirm", methods=["GET", "POST"])



def delete_account_confirm():



    redirect_response = login_required()







    if redirect_response:



        return redirect_response







    if not session.get("delete_verified"):



        return redirect(url_for("account"))







    if request.method == "GET":



        return render_template("delete_account_confirm.html")







    connection = get_db_connection()







    user = connection.execute(



        """



        SELECT username, email



        FROM users



        WHERE id = ?



        """,



        (session["user_id"],)



    ).fetchone()







    if user is None:



        connection.close()



        session.clear()



        return redirect(url_for("login"))







    deleted_at = datetime.now().isoformat()







    connection.execute(



        """



        INSERT INTO deleted_users



        (username, email, deleted_at)



        VALUES (?, ?, ?)



        """,



        (



            user["username"],



            user["email"],



            deleted_at



        )



    )







    connection.execute(



        """



        DELETE FROM expenses



        WHERE user_id = ?



        """,



        (session["user_id"],)



    )







    connection.execute(



        """



        DELETE FROM password_reset_otps



        WHERE user_id = ?



        """,



        (session["user_id"],)



    )







    connection.execute(



        """



        DELETE FROM account_delete_otps



        WHERE user_id = ?



        """,



        (session["user_id"],)



    )







    connection.execute(



        """



        DELETE FROM users



        WHERE id = ?



        """,



        (session["user_id"],)



    )







    connection.commit()



    connection.close()







    try:



        send_account_deleted_email(



            user["email"],



            user["username"]



        )



    except Exception as error:



        print("Account deletion confirmation email failed:", error)







    session.clear()







    return redirect(url_for("home"))











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















@app.route("/forgot-password", methods=["GET", "POST"])



def forgot_password():



    if request.method == "POST":



        email = request.form["email"].strip().lower()







        connection = get_db_connection()







        user = connection.execute(



            "SELECT id FROM users WHERE email = ?",



            (email,)



        ).fetchone()







        connection.close()







        if not user:



            return render_template(



                "forgot_password.html",



                error="No account is registered with that email."



            )







        # Generate a secure 6-digit OTP



        otp = f"{secrets.randbelow(1000000):06d}"







        # Hash the OTP before storing it



        otp_hash = generate_password_hash(otp)







        # OTP expires in 10 minutes



        expires_at = datetime.now() + timedelta(minutes=10)







        connection = get_db_connection()







        # Remove previous OTPs for this user



        connection.execute(



            "DELETE FROM password_reset_otps WHERE user_id = ?",



            (user["id"],)



        )







        connection.execute(



            """



            INSERT INTO password_reset_otps



            (user_id, otp_hash, expires_at)



            VALUES (?, ?, ?)



            """,



            (



                user["id"],



                otp_hash,



                expires_at.isoformat()



            )



        )







        connection.commit()



        connection.close()







        try:



            send_otp_email(email, otp)



        except Exception as e:



            print("OTP EMAIL ERROR:", e)







            return render_template(



                "forgot_password.html",



                error="Unable to send OTP. Please try again later."



            )







        return redirect(



            url_for(



                "verify_otp",



                email=email



            )



        )







    return render_template("forgot_password.html")











@app.route("/verify-otp", methods=["GET", "POST"])



def verify_otp():



    email = request.args.get("email", "").strip().lower()







    if not email:



        return redirect(url_for("forgot_password"))







    connection = get_db_connection()







    user = connection.execute(



        "SELECT id FROM users WHERE email = ?",



        (email,)



    ).fetchone()







    if not user:



        connection.close()



        return redirect(url_for("forgot_password"))







    if request.method == "POST":







        otp = request.form["otp"].strip()







        reset_record = connection.execute(



            """



            SELECT id, otp_hash, expires_at



            FROM password_reset_otps



            WHERE user_id = ?



            ORDER BY id DESC



            LIMIT 1



            """,



            (user["id"],)



        ).fetchone()







        if not reset_record:



            connection.close()







            return render_template(



                "verify_otp.html",



                email=email,



                error="No valid OTP was found. Please request a new one."



            )







        expires_at = datetime.fromisoformat(



            reset_record["expires_at"]



        )







        if datetime.now() > expires_at:







            connection.execute(



                "DELETE FROM password_reset_otps WHERE user_id = ?",



                (user["id"],)



            )







            connection.commit()



            connection.close()







            return render_template(



                "verify_otp.html",



                email=email,



                error="OTP has expired. Please request a new one."



            )







        if not check_password_hash(



            reset_record["otp_hash"],



            otp



        ):



            connection.close()







            return render_template(



                "verify_otp.html",



                email=email,



                error="Invalid OTP."



            )







        # OTP is valid



        connection.execute(



            "DELETE FROM password_reset_otps WHERE user_id = ?",



            (user["id"],)



        )







        connection.commit()



        connection.close()







        session["reset_user_id"] = user["id"]







        return redirect(url_for("reset_password"))







    connection.close()







    return render_template(



        "verify_otp.html",



        email=email



    )











@app.route("/reset-password", methods=["GET", "POST"])



def reset_password():



    user_id = session.get("reset_user_id")







    if not user_id:



        return redirect(url_for("forgot_password"))







    if request.method == "POST":



        password = request.form["password"]



        confirm_password = request.form["confirm_password"]







        if len(password) < 8:



            return render_template(



                "reset_password.html",



                error="Password must be at least 8 characters long."



            )







        if password != confirm_password:



            return render_template(



                "reset_password.html",

                error="Passwords do not match."

            )
        password_hash = generate_password_hash(password)
        connection = get_db_connection()
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (password_hash, user_id)
        )
        connection.commit()
        connection.close()
        session.pop("reset_user_id", None)
        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/google4bec94f3a0690fd4.html")
def google_site_verification():
    return send_from_directory(
        Path(__file__).resolve().parent,
        "google4bec94f3a0690fd4.html"
    )



if __name__ == "__main__":

    app.run(debug=True)