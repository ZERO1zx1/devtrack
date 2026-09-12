"""User data-access functions."""

from models import execute, query


def create_user(username, email, password_hash):
    return execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash),
    )


def get_user_by_username(username):
    return query(
        "SELECT * FROM users WHERE username = ?", (username,), one=True
    )


def get_user_by_email(email):
    return query("SELECT * FROM users WHERE email = ?", (email,), one=True)


def get_user_by_id(user_id):
    return query(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (user_id,),
        one=True,
    )