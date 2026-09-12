"""Authentication business logic."""

from flask import current_app

from ..models.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    hash_password,
    verify_password,
)
from ..utils.validators import validate_registration


def register_user(username, email, password):
    """Create a user after validation.

    Returns ``(user_dict, errors)``. ``user_dict`` is ``None`` on failure.
    """
    errors = validate_registration(username, email, password)
    if not errors and get_user_by_username(username):
        errors.append("That username is already taken.")
    if not errors and get_user_by_email(email):
        errors.append("An account with that email already exists.")

    if errors:
        return None, errors

    owner_email = current_app.config.get("BOOTSTRAP_OWNER_EMAIL", "").strip().lower()
    system_role = "owner" if owner_email and email == owner_email else "member"
    user_id = create_user(username, email, hash_password(password), system_role)
    return {"id": user_id, "username": username, "system_role": system_role}, []


def authenticate(username, password):
    """Return the user dict when credentials match, else ``None``."""
    user = get_user_by_username(username)
    if user and verify_password(user, password):
        return user
    return None
