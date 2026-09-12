"""Task REST API and analytics data.

Endpoints:
    GET    /api/tasks            list (query: status, priority, q)
    POST   /api/tasks            create
    PUT    /api/tasks/<id>       update (partial)
    DELETE /api/tasks/<id>       delete
    GET    /api/analytics        dashboard numbers + activity + streaks
"""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request, session

from models import get_db
from models.project import get_project
from models.task import (
    completed_dates,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    stats,
    update_task,
    weekly_counts,
)
from routes import api_login_required

bp = Blueprint("tasks", __name__)

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "completed"}
MAX_TITLE = 200
MAX_DESCRIPTION = 1000


def check_project_belongs(project_id, user_id):
    """Return None when the project is missing or owned by someone else."""
    if project_id is None:
        return None
    project = get_project(project_id, user_id)
    if project is None:
        return f"Project {project_id} does not exist."
    return None


def validate_payload(payload, partial=False):
    """Validate a task payload. Returns (errors, normalized_update)."""
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
            errors.append(f"Description must be {MAX_DESCRIPTION} characters or fewer.")
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
        if isinstance(project_id, bool) or not isinstance(project_id, int):
            errors.append("project_id must be an integer or null.")
        else:
            fields["project_id"] = project_id

    return errors, fields


@bp.get("/api/tasks")
@api_login_required
def api_list_tasks():
    user_id = session["user_id"]
    status = request.args.get("status")
    priority = request.args.get("priority")
    q = request.args.get("q", "").strip()
    tasks = list_tasks(user_id, status=status, priority=priority, q=q)
    return jsonify({"tasks": tasks})


@bp.post("/api/tasks")
@api_login_required
def api_create_task():
    user_id = session["user_id"]
    errors, fields = validate_payload(request.get_json(silent=True))
    fields.setdefault("priority", "medium")

    project_error = check_project_belongs(fields.get("project_id"), user_id)
    if project_error:
        errors.append(project_error)

    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    task = create_task(
        user_id,
        fields["title"],
        description=fields.get("description", ""),
        priority=fields.get("priority", "medium"),
        project_id=fields.get("project_id"),
    )
    return jsonify({"task": task}), 201


@bp.put("/api/tasks/<int:task_id>")
@api_login_required
def api_update_task(task_id):
    user_id = session["user_id"]
    task = get_task(task_id, user_id)
    if task is None:
        return jsonify({"error": "Task not found."}), 404

    errors, fields = validate_payload(request.get_json(silent=True), partial=True)
    project_error = check_project_belongs(fields.get("project_id"), user_id)
    if project_error:
        errors.append(project_error)

    if errors:
        return jsonify({"error": errors[0], "errors": errors}), 400

    updated = update_task(task_id, user_id, fields)
    return jsonify({"task": updated})


@bp.delete("/api/tasks/<int:task_id>")
@api_login_required
def api_delete_task(task_id):
    user_id = session["user_id"]
    deleted = delete_task(task_id, user_id)
    if not deleted:
        return jsonify({"error": "Task not found."}), 404
    return jsonify({"ok": True}), 204


@bp.get("/api/analytics")
@api_login_required
def api_analytics():
    user_id = session["user_id"]

    counts = stats(user_id)
    dates = completed_dates(user_id)
    activity = {}
    for d in dates:
        activity[d] = activity.get(d, 0) + 1

    dates_set = set(dates)
    current_streak, longest_streak = compute_streaks(dates_set)

    return jsonify(
        {
            **counts,
            "activity": activity,
            "weekly": weekly_counts(user_id),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }
    )


def compute_streaks(dates_set):
    """Current and longest streak of consecutive days with activity."""
    today = date.today()
    today_iso = today.isoformat()

    # A streak is not broken if today is simply not finished yet.
    anchor = (
        today
        if today_iso in dates_set
        else (today - timedelta(days=1) if (today - timedelta(days=1)).isoformat() in dates_set else None)
    )
    current = 0
    if anchor:
        d = anchor
        while d.isoformat() in dates_set:
            current += 1
            d -= timedelta(days=1)

    previous = None
    longest = 0
    run = 0
    for d in sorted(dates_set):
        day = date.fromisoformat(d)
        if previous and day == previous + timedelta(days=1):
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        previous = day

    return current, longest