
import sqlite3
import pandas as pd
import os

DB_FILE = "finance_data.db"

def init_db():
    """Initializes the SQLite database with necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Transactions Table (Income/Expense)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    type TEXT, -- 'Income', 'Expense'
                    category TEXT,
                    amount REAL,
                    currency TEXT,
                    description TEXT
                )''')
    
    # Portfolio Table (Holdings)
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_type TEXT, -- 'Fund', 'Stock', 'Crypto', 'Gold', 'USD'
                    symbol TEXT,
                    quantity REAL,
                    avg_cost REAL
                )''')
                
    # History Table (Net Worth Snapshots)
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    date TEXT PRIMARY KEY,
                    net_worth REAL,
                    cash_balance REAL,
                    portfolio_value REAL
                )''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

def add_transaction(date, type, category, amount, currency, description):
    """Adds a new transaction to the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, type, category, amount, currency, description) VALUES (?, ?, ?, ?, ?, ?)",
              (date, type, category, amount, currency, description))
    conn.commit()
    conn.close()

def get_transactions():
    """Returns all transactions as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df

def get_portfolio():
    """Returns current portfolio holdings."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM portfolio", conn)
    conn.close()
    return df

def update_portfolio(asset_type, symbol, quantity, price, action):
    """
    Updates portfolio based on Buy/Sell action.
    action: 'Buy' or 'Sell'
    """
    conn = get_connection()
    c = conn.cursor()
    
    # Check if asset exists
    c.execute("SELECT id, quantity, avg_cost FROM portfolio WHERE symbol = ?", (symbol,))
    row = c.fetchone()
    
    if action == "Buy":
        if row:
            # Update existing
            curr_id, curr_qty, curr_avg = row
            new_qty = curr_qty + quantity
            # Weighted Average Cost
            new_avg = ((curr_qty * curr_avg) + (quantity * price)) / new_qty
            c.execute("UPDATE portfolio SET quantity = ?, avg_cost = ? WHERE id = ?", (new_qty, new_avg, curr_id))
        else:
            # Insert new
            c.execute("INSERT INTO portfolio (asset_type, symbol, quantity, avg_cost) VALUES (?, ?, ?, ?)",
                      (asset_type, symbol, quantity, price))
                      
    elif action == "Sell":
        if row:
            curr_id, curr_qty, curr_avg = row
            if quantity >= curr_qty:
                # Sold all
                c.execute("DELETE FROM portfolio WHERE id = ?", (curr_id,))
            else:
                # Reduce quantity (Avg Cost doesn't change on sell)
                new_qty = curr_qty - quantity
                c.execute("UPDATE portfolio SET quantity = ? WHERE id = ?", (new_qty, curr_id))
        else:
            # Selling something we don't have? 
            # For now, ignore or maybe allow shorting? Let's assume no shorting.
            pass
            
    conn.commit()
    conn.close()

def delete_transaction(trans_id):
    """Deletes a transaction by ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    conn.close()

def update_transaction(trans_id, date, type, category, amount, currency, description):
    """Updates an existing transaction."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE transactions 
        SET date = ?, type = ?, category = ?, amount = ?, currency = ?, description = ?
        WHERE id = ?
    """, (date, type, category, amount, currency, description, trans_id))
    conn.commit()
    conn.close()

def delete_portfolio_asset(asset_id):
    """Deletes a portfolio asset by ID and removes associated transactions."""
    conn = get_connection()
    c = conn.cursor()
    
    # Get symbol first
    c.execute("SELECT symbol FROM portfolio WHERE id = ?", (asset_id,))
    row = c.fetchone()
    
    if row:
        symbol = row[0]
        # Delete from portfolio
        c.execute("DELETE FROM portfolio WHERE id = ?", (asset_id,))
        
        # Delete associated transactions (Investment type, description contains symbol)
        # We look for descriptions starting with "{symbol} " (e.g. "BTC Alış", "BTC Satış")
        # This prevents accidental deletion of "BTC-USD" when deleting "BTC" if we just used LIKE '%symbol%'
        c.execute("DELETE FROM transactions WHERE category = 'Yatırım' AND description LIKE ?", (f"{symbol} %",))
        
    conn.commit()
    conn.close()

def edit_portfolio_asset(asset_id, quantity, avg_cost):
    """Directly edits a portfolio asset's quantity and average cost (for corrections)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE portfolio SET quantity = ?, avg_cost = ? WHERE id = ?", (quantity, avg_cost, asset_id))
    conn.commit()
    conn.close()

def save_daily_snapshot(date, net_worth, cash_balance, portfolio_value):
    """Saves or updates the daily net worth snapshot."""
    conn = get_connection()
    c = conn.cursor()
    # UPSERT logic: Insert or Replace
    c.execute("""
        INSERT OR REPLACE INTO history (date, net_worth, cash_balance, portfolio_value)
        VALUES (?, ?, ?, ?)
    """, (date, net_worth, cash_balance, portfolio_value))
    conn.commit()
    conn.close()

def get_history():
    """Returns historical net worth data."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM history ORDER BY date ASC", conn)
    conn.close()
    return df

def reset_db():
    """Drops all tables and re-initializes the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS transactions")
    c.execute("DROP TABLE IF EXISTS portfolio")
    c.execute("DROP TABLE IF EXISTS history")
    conn.commit()
    conn.close()
    init_db()
