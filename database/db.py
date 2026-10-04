import sqlite3
import os
from flask import g
from config import Config


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    with app.app_context():
        db = get_db()
        with app.open_resource('database/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    app.teardown_appcontext(close_db)


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(username, email, password_hash):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash)
    )
    db.commit()
    return cursor.lastrowid


def get_user_by_id(user_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_username(username):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_email(email):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def update_user(user_id, username, email):
    db = get_db()
    db.execute(
        "UPDATE users SET username = ?, email = ? WHERE id = ?",
        (username, email, user_id)
    )
    db.commit()


# ── Conversation CRUD ─────────────────────────────────────────────────────────

def create_conversation(user_id, title):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    db.commit()
    return cursor.lastrowid


def get_conversations_by_user(user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    ).fetchall()


def get_conversation_by_id(conversation_id, user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    ).fetchone()


def update_conversation_title(conversation_id, user_id, title):
    db = get_db()
    db.execute(
        "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (title, conversation_id, user_id)
    )
    db.commit()


def delete_conversation(conversation_id, user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def get_conversation_count(user_id):
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) as cnt FROM conversations WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    return row['cnt'] if row else 0


# ── Message CRUD ──────────────────────────────────────────────────────────────

def add_message(conversation_id, role, content):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content)
    )
    db.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    db.commit()
    return cursor.lastrowid


def get_messages_by_conversation(conversation_id, user_id):
    db = get_db()
    # Verify ownership before fetching messages
    conv = db.execute(
        "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    ).fetchone()
    if not conv:
        return []
    return db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,)
    ).fetchall()


# ── Document CRUD ─────────────────────────────────────────────────────────────

def save_document(user_id, filename, original_filename, file_type, extracted_text):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO documents (user_id, filename, original_filename, file_type, extracted_text)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, filename, original_filename, file_type, extracted_text)
    )
    db.commit()
    return cursor.lastrowid


def get_documents_by_user(user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()


def get_document_by_id(doc_id, user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM documents WHERE id = ? AND user_id = ?",
        (doc_id, user_id)
    ).fetchone()


def delete_document(doc_id, user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM documents WHERE id = ? AND user_id = ?",
        (doc_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def get_document_count(user_id):
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) as cnt FROM documents WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    return row['cnt'] if row else 0
