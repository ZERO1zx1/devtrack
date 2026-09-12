"""Blueprint registration and shared route guards."""

from functools import wraps

from flask import Blueprint, jsonify, redirect, request, session, url_for


def login_required(view):
    """Redirect anonymous users to the login page."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def api_login_required(view):
    """Return 401 JSON for anonymous API calls."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Authentication required."}), 401
        return view(*args, **kwargs)

    return wrapper


def register_blueprints(app):
    """Attach all route blueprints to the Flask app."""
    from routes.auth import bp as auth_bp
    from routes.projects import bp as projects_bp
    from routes.tasks import bp as tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(projects_bp)