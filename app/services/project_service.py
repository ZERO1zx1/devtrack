"""Project business logic — thin layer between routes and the data model."""

from ..models import project as project_model
from ..utils.validators import validate_project_payload


def create_project(user_id, payload):
    """Create a project from a request payload.

    Returns ``(project_dict, errors)``.
    """
    errors, fields = validate_project_payload(payload)
    if errors:
        return None, errors

    project = project_model.create_project(
        user_id,
        fields["name"],
        description=fields.get("description", ""),
        start_date=fields.get("start_date"),
        deadline=fields.get("deadline"),
    )
    return project, []


def update_project(user_id, project_id, payload):
    """Update a project from a request payload.

    Returns ``(project_dict, errors)``.
    """
    if project_model.get_project(project_id, user_id) is None:
        return None, ["Project not found."]

    errors, fields = validate_project_payload(payload, partial=True)
    if errors:
        return None, errors

    project = project_model.update_project(project_id, user_id, fields)
    return project, []


def delete_project(user_id, project_id):
    """Delete a project. Returns ``True`` when a row was removed."""
    return bool(project_model.delete_project(project_id, user_id))