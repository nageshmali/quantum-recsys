import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            genre_prefs   TEXT DEFAULT '[]',
            is_new_user   INTEGER DEFAULT 1,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS watch_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            movie_id   INTEGER NOT NULL,
            movie_title TEXT NOT NULL,
            action     TEXT DEFAULT 'viewed',
            timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            movie_id    INTEGER NOT NULL,
            movie_title TEXT NOT NULL,
            added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, movie_id)
        )
    ''')

    conn.commit()
    conn.close()


def register_user(username, email, password):
    """Register a new user. Returns (success, message)."""
    try:
        password_hash = generate_password_hash(password)

        conn = sqlite3.connect(DB_PATH)
        c    = conn.cursor()
        c.execute(
            '''INSERT INTO users
               (username, email, password_hash)
               VALUES (?, ?, ?)''',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        return True, "Registration successful"

    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return False, "Username already exists"
        elif 'email' in str(e):
            return False, "Email already registered"
        return False, "Registration failed"


def login_user(username, password):
    """Verify login. Returns (success, user_data)."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        'SELECT * FROM users WHERE username = ?',
        (username,)
    )
    user = c.fetchone()
    conn.close()

    if not user:
        return False, None

    stored_hash = user[3].encode('utf-8')
    if check_password_hash(user[3], password):
        return True, {
            'id'          : user[0],
            'username'    : user[1],
            'email'       : user[2],
            'genre_prefs' : json.loads(user[4]),
            'is_new_user' : user[5]
        }
    return False, None


def save_genre_prefs(username, genres):
    """Save user genre preferences."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        '''UPDATE users
           SET genre_prefs = ?, is_new_user = 0
           WHERE username = ?''',
        (json.dumps(genres), username)
    )
    conn.commit()
    conn.close()


def add_to_watch_history(username, movie_id, movie_title):
    """Log a movie view."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        '''INSERT INTO watch_history
           (username, movie_id, movie_title)
           VALUES (?, ?, ?)''',
        (username, movie_id, movie_title)
    )
    conn.commit()
    conn.close()


def get_watch_history(username, limit=50):
    """Get user's watch history."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        '''SELECT movie_id, movie_title, timestamp
           FROM watch_history
           WHERE username = ?
           ORDER BY timestamp DESC
           LIMIT ?''',
        (username, limit)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def add_to_watchlist(username, movie_id, movie_title):
    """Add movie to watchlist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c    = conn.cursor()
        c.execute(
            '''INSERT INTO watchlist
               (username, movie_id, movie_title)
               VALUES (?, ?, ?)''',
            (username, movie_id, movie_title)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_watchlist(username):
    """Get user's watchlist."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        '''SELECT movie_id, movie_title, added_at
           FROM watchlist
           WHERE username = ?
           ORDER BY added_at DESC''',
        (username,)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_user(username):
    """Get user data."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        'SELECT * FROM users WHERE username = ?',
        (username,)
    )
    user = c.fetchone()
    conn.close()
    if user:
        return {
            'id'         : user[0],
            'username'   : user[1],
            'email'      : user[2],
            'genre_prefs': json.loads(user[4]),
            'is_new_user': user[5]
        }
    return None