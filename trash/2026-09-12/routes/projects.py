"""Project pages and REST API."""

from flask import Blueprint, jsonify, render_template, request, session

from models.project import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from routes import api_login_required, login_required

bp = Blueprint("projects", __name__)

MAX_NAME = 120
MAX_DESCRIPTION = 800


def validate_payload(payload, partial=False):
    errors = []
    fields = {}

    if not isinstance(payload, dict):
        return ["Request body must be a JSON object."], {}

    name = payload.get("name")
    if name is not None:
        name = str(name).strip()
        if not name:
            errors.append("Project name is required.")
        elif len(name) > MAX_NAME:
            errors.append(f"Project name must be {MAX_NAME} characters or fewer.")
        else:
            fields["name"] = name
    elif not partial:
        errors.append("Project name is required.")

    description = payload.get("description")
    if description is not None:
        description = str(description).strip()
        if len(description) > MAX_DESCRIPTION:
            errors.append(f"Description must be {MAX_DESCRIPTION} characters or fewer.")
        else:
            fields["description"] = description

    for key in ("start_date", "deadline"):
        value = payload.get(key)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, str):
                errors.append(f"{key} must be an ISO date string or null.")
            else:
                fields[key] = value

    return errors, fields


def read_json():
    """Read a JSON body, rejecting wrong content types and bad JSON."""
    payload = request.get_json(silent=True)
    if payload is None:
        if not request.is_json:
            return None, "Content-Type must be application/json."
        return None, "Request body must be a valid JSON object."
    return payload, None


@bp.get("/projects")
@login_required
def projects_page():
    return render_template("projects.html")


@bp.get("/api/projects")
@api_login_required
def api_list_projects():
    projects = list_projects(session["user_id"])
    return jsonify({"projects": projects})


@bp.post("/api/projects")
@api_login_required
def api_create_project():
    payload, payload_error = read_json()
    if payload_error:
        return jsonify({"error": payload_error}), 400
    errors, fields = validate_payload(payload)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    project = create_project(
        session["user_id"],
        fields["name"],
        description=fields.get("description", ""),
        start_date=fields.get("start_date"),
        deadline=fields.get("deadline"),
    )
    return jsonify({"project": project}), 201


@bp.put("/api/projects/<int:project_id>")
@api_login_required
def api_update_project(project_id):
    user_id = session["user_id"]
    if get_project(project_id, user_id) is None:
        return jsonify({"error": "Project not found."}), 404

    payload, payload_error = read_json()
    if payload_error:
        return jsonify({"error": payload_error}), 400
    errors, fields = validate_payload(payload, partial=True)
    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    project = update_project(project_id, user_id, fields)
    return jsonify({"project": project})


@bp.delete("/api/projects/<int:project_id>")
@api_login_required
def api_delete_project(project_id):
    user_id = session["user_id"]
    deleted = delete_project(project_id, user_id)
    if not deleted:
        return jsonify({"error": "Project not found."}), 404
    return jsonify({"ok": True}), 204