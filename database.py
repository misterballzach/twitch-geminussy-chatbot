import sqlite3
import datetime

DB_FILE = "bot_memory.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            message_count INTEGER NOT NULL DEFAULT 0,
            is_subscriber BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    migrate_tables()

def migrate_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "favouritism_score" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN favouritism_score INTEGER NOT NULL DEFAULT 0")
    if "last_seen" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP")
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def create_or_update_user(username, message_count_increment=0, is_subscriber=None, favouritism_score_increment=0):
    conn = get_db_connection()
    user = get_user(username)
    now = datetime.datetime.now()
    if user is None:
        conn.execute(
            "INSERT INTO users (username, message_count, is_subscriber, favouritism_score, last_seen) VALUES (?, ?, ?, ?, ?)",
            (username, message_count_increment, 1 if is_subscriber else 0, favouritism_score_increment, now)
        )
    else:
        new_message_count = user["message_count"] + message_count_increment
        new_is_subscriber = is_subscriber if is_subscriber is not None else user["is_subscriber"]
        new_favouritism_score = user["favouritism_score"] + favouritism_score_increment
        conn.execute(
            "UPDATE users SET message_count = ?, is_subscriber = ?, favouritism_score = ?, last_seen = ? WHERE username = ?",
            (new_message_count, 1 if new_is_subscriber else 0, new_favouritism_score, now, username)
        )
    conn.commit()
    conn.close()

def set_favouritism_score(username, score):
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET favouritism_score = ? WHERE username = ?",
        (score, username)
    )
    conn.commit()
    conn.close()

def get_random_active_user():
    conn = get_db_connection()
    # Get users who have been active in the last hour and have sent at least 5 messages
    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    user = conn.execute(
        "SELECT * FROM users WHERE last_seen > ? AND message_count > 5 ORDER BY RANDOM() LIMIT 1",
        (one_hour_ago,)
    ).fetchone()
    conn.close()
    return user

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")
