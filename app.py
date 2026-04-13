from flask import Flask, render_template, request, redirect, session
import bank

app = Flask(__name__)
app.secret_key = "atm_secret"

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
        name = request.form["name"]
        pin = request.form["pin"]

        card = bank.create_account(name, pin)

        return render_template("card.html", card=card)

    return render_template("create.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        card = request.form["card"]
        pin = request.form["pin"]

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

    balance = bank.check_balance(session["user_id"])
    statement = bank.mini_statement(session["user_id"])

    return render_template("dashboard.html", balance=balance, statement=statement)

# ---------- DEPOSIT ----------
@app.route("/deposit", methods=["POST"])
def deposit():
    if "user_id" not in session:
        return redirect("/")

    amount = float(request.form["amount"])
    bank.deposit(session["user_id"], amount)

    return redirect("/dashboard")

# ---------- WITHDRAW ----------
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if "user_id" not in session:
        return redirect("/")

    amount = float(request.form["amount"])

    if not bank.withdraw(session["user_id"], amount):
        return "❌ Insufficient Balance"

    return redirect("/dashboard")

# ---------- CHANGE PIN ----------
@app.route("/change_pin", methods=["POST"])
def change_pin():
    if "user_id" not in session:
        return redirect("/")

    new_pin = request.form["pin"]
    bank.change_pin(session["user_id"], new_pin)

    return redirect("/dashboard")

# ---------- DELETE ACCOUNT ----------
@app.route("/delete")
def delete():
    if "user_id" not in session:
        return redirect("/")

    bank.delete_account(session["user_id"])
    session.clear()

    return "✅ Account Deleted Successfully"

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)