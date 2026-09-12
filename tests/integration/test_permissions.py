"""HTTP authorization guard and schema upgrade tests."""

import sqlite3

from flask import Blueprint

from app import create_app
from app.models import user as user_model
from app.utils.decorators import api_permission_required, permission_required
from tests.conftest import login, register


def _register_guarded_routes(app):
    bp = Blueprint("permission_test", __name__)

    @bp.get("/test/moderation")
    @permission_required("moderate_content")
    def moderation_page():
        return "allowed"

    @bp.get("/api/test/admin")
    @api_permission_required("manage_members")
    def admin_api():
        return {"ok": True}

    app.register_blueprint(bp)


def test_html_permission_guard_redirects_or_forbids(client, app):
    _register_guarded_routes(app)
    assert client.get("/test/moderation").status_code == 302
    register(client)
    login(client)
    assert client.get("/test/moderation").status_code == 403


def test_api_permission_guard_reads_current_database_role(client, app):
    _register_guarded_routes(app)
    register(client)
    login(client)

    denied = client.get("/api/test/admin")
    assert denied.status_code == 403
    assert denied.get_json() == {"ok": False, "error": "Permission denied."}

    with app.app_context():
        user = user_model.get_user_by_username("dev")
        user_model.update_system_role(user["id"], "admin")

    allowed = client.get("/api/test/admin")
    assert allowed.status_code == 200
    assert allowed.get_json() == {"ok": True}


def test_api_permission_guard_returns_401_for_anonymous(client, app):
    _register_guarded_routes(app)
    response = client.get("/api/test/admin")
    assert response.status_code == 401
    assert response.get_json() == {"ok": False, "error": "Authentication required."}


def test_legacy_database_is_upgraded_with_member_role(tmp_path, monkeypatch):
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT
        )"""
    )
    connection.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        ("legacy", "legacy@example.com", "unused"),
    )
    connection.commit()
    connection.close()

    monkeypatch.setenv("DATABASE", str(database))
    upgraded_app = create_app("testing")
    with upgraded_app.app_context():
        user = user_model.get_user_by_username("legacy")
    assert user["system_role"] == "member"
