"""Authentication routes: register, login, logout.

Passwords are stored as hashes only (werkzeug's scrypt-based default)
and user state lives in Flask's signed session cookie.
"""

import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import execute, query
from models.user import create_user, get_user_by_email, get_user_by_username

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _valid_username(username):
    return bool(
        USERNAME_RE.match(username) and 3 <= len(username) <= 50
    )


def _valid_email(email):
    return "@" in email and len(email) <= 120


def _valid_password(password):
    return 6 <= len(password) <= 128


def _validate_registration(username, email, password):
    errors = []
    if not _valid_username(username):
        errors.append("Username must be 3-50 chars: letters, numbers or underscores.")
    if not _valid_email(email):
        errors.append("Please provide a valid email address.")
    if not _valid_password(password):
        errors.append("Password must be between 6 and 128 characters.")
    return errors


@bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = _validate_registration(username, email, password)
        if not errors:
            if get_user_by_username(username):
                errors.append("That username is already taken.")
            elif get_user_by_email(email):
                errors.append("An account with that email already exists.")

        if not errors:
            password_hash = generate_password_hash(password)
            create_user(username, email, password_hash)
            flash("Account created. Welcome to DevTrack!", "success")
            return redirect(url_for("auth.login"))

        for error in errors:
            flash(error, "error")

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(request.args.get("next") or url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))