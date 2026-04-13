import sqlite3
from datetime import datetime
import random

DB = "bank.db"

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
    conn = get_db()
    cur = conn.cursor()

    card = generate_card()

    cur.execute("""
    INSERT INTO users (name, card_number, pin, balance)
    VALUES (?, ?, ?, ?)
    """, (name, card, pin, 0))

    conn.commit()
    conn.close()

    return card   # RETURN CARD NUMBER

# ---------- LOGIN ----------
def login(card_number, pin):
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
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE users SET balance = balance + ? WHERE id=?",
                (amount, user_id))

    cur.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?)",
                (user_id, "Deposit", amount, datetime.now()))

    conn.commit()
    conn.close()

def withdraw(user_id, amount):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    balance = cur.fetchone()[0]

    if balance >= amount:
        cur.execute("UPDATE users SET balance = balance - ? WHERE id=?",
                    (amount, user_id))

        cur.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?)",
                    (user_id, "Withdraw", amount, datetime.now()))

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
    balance = cur.fetchone()[0]

    conn.close()
    return balance

def change_pin(user_id, new_pin):
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