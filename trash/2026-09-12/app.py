"""DevTrack — a full-stack developer task & progress tracker.

Run with::

    python app.py

Requires Flask and SQLite3. The database is created automatically
under ``instance/devtrack.db``.
"""

import os
import sqlite3

from flask import Flask, render_template, session

import models
from models.project import list_projects
from models.task import stats
from routes import login_required, register_blueprints


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devtrack-dev-secret")
    app.config["DATABASE"] = os.path.join(app.instance_path, "devtrack.db")

    if test_config:
        app.config.update(test_config)

    models.init_app(app)

    with app.app_context():
        models.init_db()

    register_blueprints(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/dashboard")
    @login_required
    def dashboard():
        user_id = session["user_id"]
        return render_template(
            "dashboard.html",
            stats=stats(user_id),
            projects=list_projects(user_id),
        )

    @app.errorhandler(404)
    def not_found(_err):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_err):
        return render_template("500.html"), 500

    @app.errorhandler(sqlite3.IntegrityError)
    def integrity_error(_err):
        return render_template("500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))