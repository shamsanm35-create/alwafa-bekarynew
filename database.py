import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "/home/ubuntu/alwafaa_bakery/bakery.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Production table
    c.execute('''CREATE TABLE IF NOT EXISTS production (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    flour_bags REAL,
                    expected_production INTEGER
                )''')
    
    # Sales table
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    distributor TEXT,
                    delivered INTEGER,
                    returned INTEGER,
                    net_sales INTEGER,
                    price_per_unit REAL,
                    total_amount REAL,
                    cash_paid REAL
                )''')
    
    # Other sales table
    c.execute('''CREATE TABLE IF NOT EXISTS other_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    item_name TEXT,
                    amount REAL
                )''')
    
    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    labor REAL,
                    wood REAL,
                    misc REAL,
                    total_expenses REAL
                )''')
    
    # Ledger table (Credit/Debit)
    c.execute('''CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    name TEXT,
                    description TEXT,
                    debit REAL DEFAULT 0,  -- عليه (Debt)
                    credit REAL DEFAULT 0  -- له (Payment/Credit)
                )''')
    
    # Settings table for prices
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value REAL
                )''')
    
    # Initialize default prices if not exist
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_distributor', 16)")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_cash', 20)")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_factory', 15)")
    
    # Distributor prices table
    c.execute('''CREATE TABLE IF NOT EXISTS distributor_prices (
                    distributor TEXT PRIMARY KEY,
                    price REAL
                )''')
    
    # Default distributors
    dists = ["هيثم", "وجيه", "المفرش", "علي", "درهم"]
    for d in dists:
        c.execute("INSERT OR IGNORE INTO distributor_prices (distributor, price) VALUES (?, 16)", (d,))
    
    conn.commit()
    conn.close()

def get_distributor_price(name, default=16):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT price FROM distributor_prices WHERE distributor = ?", (name,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def update_distributor_price(name, price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO distributor_prices (distributor, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()

def get_setting(key, default=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def update_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_ledger_entry(date, name, description, debit=0, credit=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO ledger (date, name, description, debit, credit) VALUES (?, ?, ?, ?, ?)",
              (date, name, description, debit, credit))
    conn.commit()
    conn.close()

def save_production(date, flour_bags, expected_production):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Check if exists for the date to update or insert
    c.execute("SELECT id FROM production WHERE date = ?", (date,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE production SET flour_bags = ?, expected_production = ? WHERE date = ?", (flour_bags, expected_production, date))
    else:
        c.execute("INSERT INTO production (date, flour_bags, expected_production) VALUES (?, ?, ?)",
                  (date, flour_bags, expected_production))
    conn.commit()
    conn.close()

def save_sales(date, distributor, delivered, returned, net_sales, price, total_amount, cash_paid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM sales WHERE date = ? AND distributor = ?", (date, distributor))
    row = c.fetchone()
    if row:
        c.execute("UPDATE sales SET delivered = ?, returned = ?, net_sales = ?, price_per_unit = ?, total_amount = ?, cash_paid = ? WHERE id = ?", 
                  (delivered, returned, net_sales, price, total_amount, cash_paid, row[0]))
    else:
        c.execute("INSERT INTO sales (date, distributor, delivered, returned, net_sales, price_per_unit, total_amount, cash_paid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (date, distributor, delivered, returned, net_sales, price, total_amount, cash_paid))
    conn.commit()
    conn.close()

def save_other_sales(date, item_name, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM other_sales WHERE date = ? AND item_name = ?", (date, item_name))
    row = c.fetchone()
    if row:
        c.execute("UPDATE other_sales SET amount = ? WHERE id = ?", (amount, row[0]))
    else:
        c.execute("INSERT INTO other_sales (date, item_name, amount) VALUES (?, ?, ?)",
                  (date, item_name, amount))
    conn.commit()
    conn.close()

def save_expenses(date, labor, wood, misc, total):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM expenses WHERE date = ?", (date,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE expenses SET labor = ?, wood = ?, misc = ?, total_expenses = ? WHERE date = ?", (labor, wood, misc, total, date))
    else:
        c.execute("INSERT INTO expenses (date, labor, wood, misc, total_expenses) VALUES (?, ?, ?, ?, ?)",
                  (date, labor, wood, misc, total))
    conn.commit()
    conn.close()

def get_data(table_name, date=None, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT * FROM {table_name}"
    params = []
    if date:
        query += " WHERE date = ?"
        params.append(date)
    elif start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

init_db()
