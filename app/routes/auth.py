"""Authentication routes built on the auth service."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services import password_reset_service
from ..services.auth_service import authenticate, register_user


def create_blueprint():
    bp = Blueprint("auth", __name__)

    @bp.route("/register", methods=["GET", "POST"])
    def register():
        if session.get("user_id"):
            return redirect(url_for("main.dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user, errors = register_user(username, email, password)
            if user:
                flash("Account created. Welcome to DevTrack!", "success")
                return redirect(url_for("auth.login"))

            for error in errors:
                flash(error, "error")

        return render_template("auth/register.html")

    @bp.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("main.dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = authenticate(username, password)
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(request.args.get("next") or url_for("main.dashboard"))

            flash("Invalid username or password.", "error")

        return render_template("auth/login.html")

    @bp.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("main.index"))

    @bp.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if session.get("user_id"):
            return redirect(url_for("main.dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            _, message = password_reset_service.request_password_reset(email)
            flash(message, "success")
            return redirect(url_for("auth.login"))

        return render_template("auth/forgot.html")

    @bp.route("/reset-password/<token>", methods=["GET", "POST"])
    def reset_password(token):
        if session.get("user_id"):
            return redirect(url_for("main.dashboard"))

        if request.method == "POST":
            password = request.form.get("password", "")
            ok, message = password_reset_service.reset_password(token, password)
            flash(message, "success" if ok else "error")
            if ok:
                return redirect(url_for("auth.login"))

        return render_template("auth/reset.html")

    return bp