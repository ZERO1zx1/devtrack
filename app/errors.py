"""Central application error handlers.

HTML pages for browser routes, JSON responses for API routes.
"""

import sqlite3

from flask import jsonify, redirect, render_template, request, url_for


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_err):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Not found."}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(401)
    def unauthorized(_err):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Authentication required."}), 401
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(_err):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Forbidden."}), 403
        return render_template("errors/500.html"), 403

    @app.errorhandler(500)
    def server_error(_err):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Internal server error."}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(sqlite3.IntegrityError)
    def integrity_error(_err):
        return jsonify({"ok": False, "error": "That record already exists."}), 409