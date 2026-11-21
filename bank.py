import sqlite3
from datetime import datetime
import random
import os
import math

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank.db")

def get_db():
    return sqlite3.connect(DB)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # UPDATED TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        card_number TEXT UNIQUE,
        pin TEXT,
        balance REAL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------- GENERATE CARD NUMBER ----------
def generate_card():
    return str(random.randint(1000000000000000, 9999999999999999))

# ---------- CREATE ACCOUNT ----------
def create_account(name, pin):
    name = str(name).strip()
    pin = str(pin).strip()
    if not name:
        raise ValueError("Name is required")
    if not pin.isdigit() or len(pin) != 4:
        raise ValueError("PIN must be exactly 4 digits")

    conn = get_db()
    cur = conn.cursor()

    try:
        while True:
            card = generate_card()
            try:
                cur.execute("""
                INSERT INTO users (name, card_number, pin, balance)
                VALUES (?, ?, ?, ?)
                """, (name, card, pin, 0))
                conn.commit()
                return card
            except sqlite3.IntegrityError:
                continue
    finally:
        conn.close()

# ---------- LOGIN ----------
def login(card_number, pin):
    card_number = str(card_number).strip()
    pin = str(pin).strip()
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM users 
    WHERE card_number=? AND pin=?
    """, (card_number, pin))

    user = cur.fetchone()
    conn.close()

    return user

# ---------- OTHER FUNCTIONS SAME ----------

def deposit(user_id, amount):
    amount = float(amount)
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Amount must be a positive finite number")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    if cur.rowcount == 0:
        conn.close()
        return False

    cur.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?)",
                (user_id, "Deposit", amount, datetime.now().isoformat()))

    conn.commit()
    conn.close()
    return True

def withdraw(user_id, amount):
    amount = float(amount)
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Amount must be a positive finite number")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET balance = balance - ? WHERE id=? AND balance >= ?",
        (amount, user_id, amount),
    )
    if cur.rowcount == 1:
        cur.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?)",
                    (user_id, "Withdraw", amount, datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return True

    conn.close()
    return False

def delete_account(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    cur.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()

def check_balance(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None

def change_pin(user_id, new_pin):
    new_pin = str(new_pin).strip()
    if not new_pin.isdigit() or len(new_pin) != 4:
        raise ValueError("PIN must be exactly 4 digits")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE users SET pin=? WHERE id=?", (new_pin, user_id))

    conn.commit()
    conn.close()

def mini_statement(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT type, amount, date 
    FROM transactions 
    WHERE user_id=? 
    ORDER BY id DESC LIMIT 5
    """, (user_id,))

    data = cur.fetchall()
    conn.close()

    return data