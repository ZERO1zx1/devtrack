"""Tests for registration, login and logout."""

from models import get_db
from tests.conftest import login, register


def test_register_creates_account(client, app):
    resp = register(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")

    with app.app_context():
        row = get_db().execute("SELECT * FROM users WHERE username = 'dev'").fetchone()
    assert row is not None
    assert row["password_hash"] != "secret123"  # never stored in plain text
    assert row["password_hash"].startswith("scrypt")


def test_register_rejects_duplicate_username(client):
    assert register(client).status_code == 302
    resp = register(client)
    assert resp.status_code == 200
    assert b"already taken" in resp.data


def test_register_validates_input(client):
    resp = register(client, username="x", email="nope", password="123")
    assert resp.status_code == 200
    assert b"3-50" in resp.data
    assert b"valid email" in resp.data
    assert b"6 and 128" in resp.data


def test_register_rejects_unapproved_chars(client):
    resp = register(client, username="bad name")
    assert resp.status_code == 200
    assert b"letters, numbers or underscores" in resp.data


def test_login_success_sets_session(client):
    register(client)
    resp = login(client)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("username") == "dev"


def test_login_wrong_password(client):
    register(client)
    resp = login(client, password="wrong-password")
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_login_unknown_user(client):
    resp = login(client, username="ghost")
    assert b"Invalid username or password" in resp.data


def test_logout_clears_session(client):
    register(client)
    login(client)
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/login")


def test_logged_in_user_reaches_dashboard(auth_client):
    resp = auth_client.get("/dashboard")
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data