from flask import Flask,render_template, request, redirect, session

import math
import os
import bank

app = Flask(__name__)
app.secret_key = os.environ.get("ATM_SECRET_KEY", "atm_secret")

# Initialize DB
bank.init_db()

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- CREATE ACCOUNT ----------
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pin = request.form.get("pin", "").strip()

        if not name:
            return render_template("create.html", error="Name is required")
        if not pin.isdigit() or len(pin) != 4:
            return render_template("create.html", error="PIN must be exactly 4 digits")

        card = bank.create_account(name, pin)

        return render_template("card.html", card=card)

    return render_template("create.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        card = request.form.get("card", "").strip()
        pin = request.form.get("pin", "").strip()

        user = bank.login(card, pin)

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return "❌ Invalid Card Number or PIN"

    return render_template("login.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    balance = bank.check_balance(user_id)
    if balance is None:
        session.clear()
        return redirect("/")

    statement = bank.mini_statement(user_id)

    return render_template("dashboard.html", balance=balance, statement=statement)

# ---------- DEPOSIT ----------
@app.route("/deposit", methods=["POST"])
def deposit():
    if "user_id" not in session:
        return redirect("/")

    try:
        amount = float(request.form.get("amount", ""))
    except (TypeError, ValueError):
        return "❌ Invalid Amount"

    if not math.isfinite(amount) or amount <= 0:
        return "❌ Invalid Amount"

    bank.deposit(session["user_id"], amount)

    return redirect("/dashboard")

# ---------- WITHDRAW ----------
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "user_id" not in session:
        return redirect("/")

    try:
        amount = float(request.form.get("amount", ""))
    except (TypeError, ValueError):
        return "❌ Invalid Amount"

    if not math.isfinite(amount) or amount <= 0:
        return "❌ Invalid Amount"

    if not bank.withdraw(session["user_id"], amount):
        return "❌ Insufficient Balance"

    return redirect("/dashboard")

# ---------- CHANGE PIN ----------
@app.route("/change_pin", methods=["POST"])
def change_pin():
    if "user_id" not in session:
        return redirect("/")

    new_pin = request.form.get("pin", "").strip()
    if not new_pin.isdigit() or len(new_pin) != 4:
        return "❌ PIN must be exactly 4 digits"

    bank.change_pin(session["user_id"], new_pin)

    return redirect("/dashboard")

# ---------- DELETE ACCOUNT ----------
@app.route("/delete", methods=["GET", "POST"])
def delete():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]

    # GET → show page
    if request.method == "GET":
        conn = bank.get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE id=?", (user_id,))
        name_row = cur.fetchone()
        conn.close()

        if name_row is None:
            session.clear()
            return redirect("/")

        return render_template("delete_confirm.html", name=name_row[0])

    # POST → check PIN and delete
    pin = request.form.get("pin", "").strip()

    conn = bank.get_db()
    cur = conn.cursor()
    cur.execute("SELECT pin FROM users WHERE id=?", (user_id,))
    pin_row = cur.fetchone()
    conn.close()

    if pin_row is None:
        session.clear()
        return redirect("/")

    if pin == pin_row[0]:
        bank.delete_account(user_id)
        session.clear()
        return render_template("delete_success.html")
    else:
        conn = bank.get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE id=?", (user_id,))
        name_row = cur.fetchone()
        conn.close()
        name = name_row[0] if name_row else "User"
        return render_template("delete_confirm.html", name=name, error="Wrong PIN")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )