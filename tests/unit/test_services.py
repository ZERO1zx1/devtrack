"""Unit tests for the service layer — no HTTP, direct function calls.

Services only need an app context so ``db`` resolves to the test database.
"""

from datetime import timedelta

import pytest

from app.models import user as user_model
from app.services import analytics_service, auth_service, project_service, task_service


def _user(app, username="svc_user"):
    with app.app_context():
        return user_model.create_user(
            username, f"{username}@example.com", user_model.hash_password("secret123")
        )


@pytest.mark.unit
def test_register_user_creates_then_authenticates(app):
    with app.app_context():
        user, errors = auth_service.register_user("svc", "svc@example.com", "secret123")
        assert user is not None
        assert errors == []
        assert auth_service.authenticate("svc", "secret123")["username"] == "svc"
        assert auth_service.authenticate("svc", "wrong-password") is None


@pytest.mark.unit
def test_register_user_duplicate_username(app):
    with app.app_context():
        auth_service.register_user("svc", "a@example.com", "secret123")
        user, errors = auth_service.register_user("svc", "b@example.com", "secret123")
        assert user is None
        assert "already taken" in errors[0]


@pytest.mark.unit
def test_register_user_duplicate_email(app):
    with app.app_context():
        auth_service.register_user("svc", "same@example.com", "secret123")
        user, errors = auth_service.register_user("other", "same@example.com", "secret123")
        assert user is None
        assert "email" in errors[0]


@pytest.mark.unit
def test_register_user_invalid_password(app):
    with app.app_context():
        user, errors = auth_service.register_user("svc", "svc@example.com", "123")
        assert user is None
        assert any("6 and 128" in e for e in errors)


@pytest.mark.unit
def test_task_service_crud_flow(app):
    uid = _user(app)
    with app.app_context():
        task, errors = task_service.create_task(uid, {"title": "Ship", "priority": "high"})
        assert errors == []
        assert task["status"] == "pending"
        assert task["priority"] == "high"

        created_id = task["id"]
        updated, errors = task_service.update_task(uid, created_id, {"status": "completed"})
        assert errors == []
        assert updated["status"] == "completed"
        assert updated["completed_at"] is not None

        assert task_service.delete_task(uid, created_id) is True
        assert task_service.list_tasks(uid) == []


@pytest.mark.unit
def test_task_service_rejects_foreign_project(app):
    uid = _user(app)
    with app.app_context():
        task, errors = task_service.create_task(uid, {"title": "X", "project_id": 999})
        assert task is None
        assert "does not exist" in errors[0]


@pytest.mark.unit
def test_task_service_update_missing_task(app):
    uid = _user(app)
    with app.app_context():
        task, errors = task_service.update_task(uid, 424242, {"title": "x"})
        assert task is None
        assert "not found" in errors[0]


@pytest.mark.unit
def test_project_service_crud(app):
    uid = _user(app)
    with app.app_context():
        project, errors = project_service.create_project(uid, {"name": "DevTrack"})
        assert errors == []
        assert project["name"] == "DevTrack"
        assert project["progress"] == 0
        assert project["tasks_count"] == 0

        updated, errors = project_service.update_project(uid, project["id"], {"name": "Renamed"})
        assert errors == []
        assert updated["name"] == "Renamed"

        assert project_service.delete_project(uid, project["id"]) is True


@pytest.mark.unit
def test_analytics_compute_streaks():
    today = __import__("datetime").date.today()
    iso = lambda ago: (today - timedelta(days=ago)).isoformat()

    dates = {iso(0), iso(1), iso(2), iso(3), iso(10), iso(11)}
    current, longest = analytics_service.compute_streaks(dates)
    assert current == 4
    assert longest == 4


@pytest.mark.unit
def test_analytics_streak_continues_through_yesterday():
    today = __import__("datetime").date.today()
    iso = lambda ago: (today - timedelta(days=ago)).isoformat()

    dates = {iso(1), iso(2), iso(3)}
    current, _ = analytics_service.compute_streaks(dates)
    assert current == 3


@pytest.mark.unit
def test_analytics_streak_broken_when_no_recent_activity():
    today = __import__("datetime").date.today()
    iso = lambda ago: (today - timedelta(days=ago)).isoformat()

    dates = {iso(5), iso(6), iso(7)}
    current, _ = analytics_service.compute_streaks(dates)
    assert current == 0