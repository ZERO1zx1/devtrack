"""Reusable route guards and shared helpers."""

from functools import wraps

from flask import abort, redirect, request, session, url_for

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


def permission_required(permission):
    """Require a platform permission for an HTML route.

    Roles are loaded from the database for every request so a stale or edited
    session cannot retain privileges after an administrator changes a role.
    """

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return redirect(url_for("auth.login", next=request.path))
            if not _user_has_permission(user_id, permission):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def api_permission_required(permission):
    """Require a platform permission for an API route (401/403 JSON)."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return json_error("Authentication required.", status=401)
            if not _user_has_permission(user_id, permission):
                return json_error("Permission denied.", status=403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _user_has_permission(user_id, permission):
    from ..models.role import has_permission
    from ..models.user import get_user_by_id

    user = get_user_by_id(user_id)
    return bool(user) and has_permission(user["system_role"], permission)
