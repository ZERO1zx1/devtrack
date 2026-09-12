"""Password-reset flow: request, email link, and redemption.

Links are single-use (replaced on each new request) and expire after an
hour. Requests never reveal whether an email is registered, protecting
against account enumeration.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import url_for

from ..models import password_reset as reset_model
from ..models.user import get_user_by_email, hash_password, update_password
from ..utils.validators import validate_password
from . import mail_service

RESET_TTL_HOURS = 1
# Same format as SQLite's datetime('now') so ``expires_at > datetime('now')``
# comparisons in the model match.
_DB_DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def _token_hash(token):
    """Always store the digest, never the raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _expires_at():
    """UTC expiry timestamp (now + TTL) in SQLite's string format."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (now + timedelta(hours=RESET_TTL_HOURS)).strftime(_DB_DT_FORMAT)


def request_password_reset(email):
    """Issue a reset token for ``email`` and email the link.

    Returns ``(ok, message)`` — the message is identical whether the account
    exists or not.
    """
    user = get_user_by_email(email)
    if user is not None:
        token = secrets.token_urlsafe(32)
        reset_model.create_reset(user["id"], _token_hash(token), _expires_at())
        reset_url = url_for("auth.reset_password", token=token, _external=True)
        mail_service.send_password_reset_email(user["email"], user["username"], reset_url)

    return True, "If that email is registered, a reset link is on its way."


def reset_password(token, new_password):
    """Validate and redeem ``token``. Returns ``(ok, message)``."""
    if not validate_password(new_password):
        return False, "Password must be between 6 and 128 characters."

    user = reset_model.find_user_by_token(_token_hash(token))
    if user is None:
        return False, "This reset link is invalid or has expired."

    update_password(user["id"], hash_password(new_password))
    reset_model.delete_resets_for_user(user["id"])
    return True, "Your password was reset. You can log in now."