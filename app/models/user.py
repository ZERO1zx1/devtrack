"""User data-access functions."""

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


def create_user(username, email, password_hash):
    return db.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash),
    )


def get_user_by_username(username):
    return db.query("SELECT * FROM users WHERE username = ?", (username,), one=True)


def get_user_by_email(email):
    return db.query("SELECT * FROM users WHERE email = ?", (email,), one=True)


def get_user_by_id(user_id):
    return db.query(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (user_id,),
        one=True,
    )


def hash_password(password):
    """Return a one-way scrypt hash — never store raw passwords."""
    return generate_password_hash(password)


def update_password(user_id, password_hash):
    """Replace a user's password hash and stamp ``updated_at``."""
    return db.execute(
        "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
        (password_hash, user_id),
    )


def verify_password(user, password):
    """Check ``password`` against the stored hash."""
    return bool(user) and check_password_hash(user["password_hash"], password)