"""Reusable route guards and shared helpers."""

from functools import wraps

from flask import redirect, request, session, url_for

from .responses import json_error


def login_required(view):
    """Redirect anonymous users to the login page."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def api_login_required(view):
    """Return 401 JSON for anonymous API calls."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return json_error("Authentication required.", status=401)
        return view(*args, **kwargs)

    return wrapped