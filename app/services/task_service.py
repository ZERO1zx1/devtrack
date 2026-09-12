"""Task business logic — thin layer between routes and the data model."""

from ..models import task as task_model
from ..models.project import get_project
from ..utils.validators import parse_json_body, validate_task_payload


def _ensure_project_belongs(project_id, user_id):
    """Return an error string when the project is missing or foreign; ``None`` otherwise."""
    if project_id is None:
        return None
    if get_project(project_id, user_id) is None:
        return f"Project {project_id} does not exist."
    return None


def list_tasks(user_id, status=None, priority=None, q=None):
    """List the user's tasks with optional status / priority / search filters."""
    q = (q or "").strip()[:100]
    return task_model.list_tasks(user_id, status=status, priority=priority, q=q)


def create_task(user_id, payload):
    """Create a task from a request payload.

    Returns ``(task_dict, errors)``. ``task_dict`` is ``None`` on failure.
    """
    errors, fields = validate_task_payload(payload)
    fields.setdefault("priority", "medium")

    project_err = _ensure_project_belongs(fields.get("project_id"), user_id)
    if project_err:
        errors.append(project_err)

    if errors:
        return None, errors

    task = task_model.create_task(
        user_id,
        fields["title"],
        description=fields.get("description", ""),
        priority=fields.get("priority", "medium"),
        project_id=fields.get("project_id"),
    )
    return task, []


def update_task(user_id, task_id, payload):
    """Update a task from a request payload.

    Returns ``(task_dict, errors)``.
    """
    task = task_model.get_task(task_id, user_id)
    if task is None:
        return None, ["Task not found."]

    errors, fields = validate_task_payload(payload, partial=True)

    project_err = _ensure_project_belongs(fields.get("project_id"), user_id)
    if project_err:
        errors.append(project_err)

    if errors:
        return None, errors

    updated = task_model.update_task(task_id, user_id, fields)
    return updated, []


def delete_task(user_id, task_id):
    """Delete a task. Returns ``True`` when a row was removed."""
    return bool(task_model.delete_task(task_id, user_id))