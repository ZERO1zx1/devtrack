"""Password-reset token data access.

Tokens are never stored in plain text — only their SHA-256 hash, so a
database leak does not hand out usable reset links.
"""

from ..extensions import db


def create_reset(user_id, token_hash, expires_at):
    """Store a token hash, revoking any previous resets for the user."""
    delete_resets_for_user(user_id)
    return db.execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires_at),
    )


def find_user_by_token(token_hash):
    """Return the owning user when the token is valid and unexpired."""
    return db.query(
        """
        SELECT u.id, u.username, u.email
        FROM password_resets pr
        JOIN users u ON u.id = pr.user_id
        WHERE pr.token_hash = ? AND pr.expires_at > datetime('now')
        """,
        (token_hash,),
        one=True,
    )


def delete_resets_for_user(user_id):
    """Remove every reset row for a user (called after a successful reset)."""
    return db.execute_affected(
        "DELETE FROM password_resets WHERE user_id = ?", (user_id,)
    )