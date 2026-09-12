"""Server-side validation helpers, shared by routes and services."""

import re

from flask import request

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")

# Length limits (mirrored by the frontend maxlength attributes).
MAX_TITLE = 200
MAX_DESCRIPTION = 1000
MAX_PROJECT_NAME = 120
MAX_PROJECT_DESCRIPTION = 800

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "completed"}
VALID_DATE_KEYS = ("start_date", "deadline")


def parse_json_body():
    """Read a JSON body; reject wrong content types and malformed JSON.

    Returns ``(payload, error_message)``.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        if not request.is_json:
            return None, "Content-Type must be application/json."
        return None, "Request body must be a valid JSON object."
    return payload, None


def validate_username(username):
    return bool(USERNAME_RE.match(username) and 3 <= len(username) <= 50)


def validate_email(email):
    return "@" in email and len(email) <= 120


def validate_password(password):
    return 6 <= len(password) <= 128


def validate_registration(username, email, password):
    """Return a list of registration error messages (empty when valid)."""
    errors = []
    if not validate_username(username):
        errors.append("Username must be 3-50 chars: letters, numbers or underscores.")
    if not validate_email(email):
        errors.append("Please provide a valid email address.")
    if not validate_password(password):
        errors.append("Password must be between 6 and 128 characters.")
    return errors


def _parse_int(value, field):
    if isinstance(value, bool) or not isinstance(value, int):
        return None, f"{field} must be an integer or null."
    return value, None


def validate_task_payload(payload, partial=False):
    """Validate a task payload.

    Returns ``(errors, normalized_fields)``. ``partial=True`` allows the
    update flow to send only the fields it wants to change.
    """
    errors = []
    fields = {}

    if not isinstance(payload, dict):
        return ["Request body must be a JSON object."], {}

    title = payload.get("title")
    if title is not None:
        title = str(title).strip()
        if not title:
            errors.append("Title is required.")
        elif len(title) > MAX_TITLE:
            errors.append(f"Title must be {MAX_TITLE} characters or fewer.")
        else:
            fields["title"] = title
    elif not partial:
        errors.append("Title is required.")

    description = payload.get("description")
    if description is not None:
        description = str(description).strip()
        if len(description) > MAX_DESCRIPTION:
            errors.append(
                f"Description must be {MAX_DESCRIPTION} characters or fewer."
            )
        else:
            fields["description"] = description

    priority = payload.get("priority")
    if priority is not None:
        if priority in VALID_PRIORITIES:
            fields["priority"] = priority
        else:
            errors.append("Priority must be low, medium or high.")

    status = payload.get("status")
    if status is not None:
        if status in VALID_STATUSES:
            fields["status"] = status
        else:
            errors.append("Status must be pending or completed.")

    project_id = payload.get("project_id")
    if project_id is not None:
        parsed, err = _parse_int(project_id, "project_id")
        if err:
            errors.append(err)
        else:
            fields["project_id"] = parsed

    return errors, fields


def validate_project_payload(payload, partial=False):
    """Validate a project payload. Returns ``(errors, normalized_fields)``."""
    errors = []
    fields = {}

    if not isinstance(payload, dict):
        return ["Request body must be a JSON object."], {}

    name = payload.get("name")
    if name is not None:
        name = str(name).strip()
        if not name:
            errors.append("Project name is required.")
        elif len(name) > MAX_PROJECT_NAME:
            errors.append(f"Project name must be {MAX_PROJECT_NAME} characters or fewer.")
        else:
            fields["name"] = name
    elif not partial:
        errors.append("Project name is required.")

    description = payload.get("description")
    if description is not None:
        description = str(description).strip()
        if len(description) > MAX_PROJECT_DESCRIPTION:
            errors.append(
                f"Description must be {MAX_PROJECT_DESCRIPTION} characters or fewer."
            )
        else:
            fields["description"] = description

    for key in VALID_DATE_KEYS:
        value = payload.get(key)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, str):
                errors.append(f"{key} must be an ISO date string or null.")
            else:
                fields[key] = value

    return errors, fields