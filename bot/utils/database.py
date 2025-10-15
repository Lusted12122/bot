# bot/utils/database.py
import sqlite3
import random
import datetime

DB_FILE = "GingaBot.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT NOT NULL,
                referrer_id INTEGER,
                bonus_balance REAL DEFAULT 0,
                game_balance INTEGER DEFAULT 500,
                purchases INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                last_bonus_date TEXT
            )
        """)
        conn.commit()

def add_user(user_id, user_name, referrer_id=None):
    """Adds a new user to the database and rewards the referrer if any."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (user_id, user_name, referrer_id, last_bonus_date) VALUES (?, ?, ?, ?)",
                           (user_id, user_name, referrer_id, None))
            if referrer_id:
                bonus = round(random.uniform(2, 5), 2)
                cursor.execute("""
                    UPDATE users
                    SET bonus_balance = bonus_balance + ?,
                        referrals = referrals + 1
                    WHERE user_id = ?
                """, (bonus, referrer_id))
        conn.commit()

def get_user_profile(user_id):
    """Retrieves a user's profile data from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT bonus_balance, game_balance, purchases, referrals FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

def update_game_balance(user_id, amount):
    """Updates a user's game balance."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET game_balance = game_balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

def get_all_users():
    """Retrieves all user IDs from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

def claim_daily_bonus(user_id):
    """Checks and gives a daily bonus to the user."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_bonus_date FROM users WHERE user_id = ?", (user_id,))
        last_date_str = cursor.fetchone()[0]
        today_str = datetime.date.today().isoformat()

        if last_date_str == today_str:
            return False  # Already claimed

        cursor.execute("UPDATE users SET game_balance = game_balance + 100, last_bonus_date = ? WHERE user_id = ?", (today_str, user_id))
        conn.commit()
        return True # Success
