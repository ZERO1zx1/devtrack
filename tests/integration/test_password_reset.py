"""Integration tests for the password-reset flow.

SMTP is never contacted here: the mailer is monkeypatched to capture the
reset link, and the fallback (no SMTP host) path is asserted directly.
"""

from datetime import datetime, timedelta, timezone

from app.models import password_reset as reset_model
from app.models.user import create_user, hash_password
from app.services import mail_service, password_reset_service
from tests.conftest import login, register

RESET_EMAIL = "dev@example.com"


def _capture_reset_link(monkeypatch, app):
    """Return a dict populated with the reset URL that would be emailed."""
    captured = {"url": None}

    def fake_send(to_email, username, reset_url):
        captured["url"] = reset_url
        return True

    monkeypatch.setattr(mail_service, "send_password_reset_email", fake_send)
    return captured


def _extract_token(reset_url):
    return reset_url.rstrip("/").rsplit("/", 1)[-1]


def test_forgot_password_page_renders(client):
    resp = client.get("/forgot-password")
    assert resp.status_code == 200
    assert b"Send Reset Link" in resp.data


def test_request_sends_link_and_redirects(client, app, monkeypatch):
    register(client)
    captured = _capture_reset_link(monkeypatch, app)

    resp = client.post("/forgot-password", data={"email": RESET_EMAIL})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    assert captured["url"] is not None
    assert "reset-password" in captured["url"]

    with app.app_context():
        rows = reset_model.find_user_by_token(
            password_reset_service._token_hash(_extract_token(captured["url"]))
        )
    assert rows is not None and rows["email"] == RESET_EMAIL


def test_request_unknown_email_does_not_leak_accounts(client, app, monkeypatch):
    captured = _capture_reset_link(monkeypatch, app)
    resp = client.post("/forgot-password", data={"email": "ghost@example.com"})
    assert resp.status_code == 302
    assert captured["url"] is None


def test_password_reset_roundtrip(client, app, monkeypatch):
    register(client)
    captured = _capture_reset_link(monkeypatch, app)
    client.post("/forgot-password", data={"email": RESET_EMAIL})

    token = _extract_token(captured["url"])

    page = client.get(f"/reset-password/{token}")
    assert page.status_code == 200
    assert b"New password" in page.data

    resp = client.post(f"/reset-password/{token}", data={"password": "new-password-123"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")

    assert login(client, password="new-password-123").status_code == 302
    client.get("/logout")

    old_login = login(client, password="secret123")
    assert old_login.status_code == 200  # old password no longer works
    assert b"Invalid username or password" in old_login.data


def test_reset_link_is_single_use(client, app, monkeypatch):
    register(client)
    captured = _capture_reset_link(monkeypatch, app)
    client.post("/forgot-password", data={"email": RESET_EMAIL})
    token = _extract_token(captured["url"])

    client.post(f"/reset-password/{token}", data={"password": "new-password-123"})
    again = client.post(f"/reset-password/{token}", data={"password": "another-pass-456"})
    assert again.status_code == 200
    assert b"invalid or has expired" in again.data


def test_reset_rejects_short_password(client, app, monkeypatch):
    register(client)
    captured = _capture_reset_link(monkeypatch, app)
    client.post("/forgot-password", data={"email": RESET_EMAIL})
    token = _extract_token(captured["url"])

    resp = client.post(f"/reset-password/{token}", data={"password": "123"})
    assert resp.status_code == 200
    assert b"6 and 128" in resp.data


def test_expired_token_rejected(app):
    with app.app_context():
        user_id = create_user("dev", RESET_EMAIL, hash_password("secret123"))
        expired = (datetime.now(timezone.utc) - timedelta(minutes=1))
        expired_str = expired.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
        reset_model.create_reset(
            user_id,
            password_reset_service._token_hash("deadbeef"),
            expired_str,
        )
        ok, message = password_reset_service.reset_password("deadbeef", "brand-new-pass")
        assert ok is False
        assert "invalid or has expired" in message


def test_mailer_falls_back_when_smtp_disabled(app):
    with app.app_context():
        sent = mail_service.send_password_reset_email("a@example.com", "dev", "http://localhost/x")
    assert sent is False