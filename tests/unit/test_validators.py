"""Unit tests for the shared validation helpers."""

import pytest

from app.utils.validators import (
    MAX_DESCRIPTION,
    MAX_PROJECT_NAME,
    MAX_TITLE,
    validate_password,
    validate_project_payload,
    validate_registration,
    validate_task_payload,
    validate_username,
)


@pytest.mark.unit
def test_valid_username():
    assert validate_username("dev_tracker")
    assert validate_username("Alto")
    assert validate_username("a" * 50)


@pytest.mark.unit
def test_invalid_usernames():
    assert not validate_username("")
    assert not validate_username("ab")  # too short
    assert not validate_username("a" * 51)  # too long
    assert not validate_username("bad name")  # space
    assert not validate_username("dash-name")  # dash
    assert not validate_username("user@dev")  # symbol


@pytest.mark.unit
def test_password_bounds():
    assert validate_password("x" * 6)
    assert validate_password("x" * 128)
    assert not validate_password("x" * 5)
    assert not validate_password("x" * 129)


@pytest.mark.unit
def test_validate_registration_ok():
    assert validate_registration("dev", "dev@example.com", "secret123") == []


@pytest.mark.unit
def test_validate_registration_reports_all_errors():
    errors = validate_registration("x", "not-an-email", "123")
    assert len(errors) == 3


@pytest.mark.unit
def test_task_title_required_when_missing():
    errors, _ = validate_task_payload({"priority": "high"})
    assert "Title is required." in errors


@pytest.mark.unit
def test_task_whitespace_title_invalid():
    errors, _ = validate_task_payload({"title": "   "})
    assert "Title is required." in errors


@pytest.mark.unit
def test_task_title_too_long():
    errors, _ = validate_task_payload({"title": "x" * (MAX_TITLE + 1)})
    assert any("200 characters" in e for e in errors)


@pytest.mark.unit
def test_task_bad_priority_rejected():
    errors, _ = validate_task_payload({"title": "ok", "priority": "urgent"})
    assert any("low, medium or high" in e for e in errors)


@pytest.mark.unit
def test_task_bad_status_rejected():
    errors, _ = validate_task_payload({"title": "ok", "status": "archived"})
    assert "Status must be pending or completed." in errors


@pytest.mark.unit
def test_task_description_too_long():
    errors, _ = validate_task_payload(
        {"title": "ok", "description": "x" * (MAX_DESCRIPTION + 1)}
    )
    assert any("1000 characters" in e for e in errors)


@pytest.mark.unit
def test_task_partial_update_allows_missing_title():
    errors, fields = validate_task_payload({"status": "completed"}, partial=True)
    assert errors == []
    assert fields == {"status": "completed"}


@pytest.mark.unit
def test_project_name_required_when_missing():
    errors, _ = validate_project_payload({"description": "nope"})
    assert "Project name is required." in errors


@pytest.mark.unit
def test_project_name_too_long():
    errors, _ = validate_project_payload({"name": "x" * (MAX_PROJECT_NAME + 1)})
    assert any("120 characters" in e for e in errors)


@pytest.mark.unit
def test_project_rejects_non_string_dates():
    errors, _ = validate_project_payload({"name": "X", "deadline": 20261231})
    assert any("ISO date string" in e for e in errors)


@pytest.mark.unit
def test_project_accepts_iso_dates():
    errors, fields = validate_project_payload(
        {"name": "X", "start_date": "2026-01-01", "deadline": "2026-12-31"}
    )
    assert errors == []
    assert fields["start_date"] == "2026-01-01"
    assert fields["deadline"] == "2026-12-31"