"""Task REST API."""

from flask import Blueprint, request, session

from ..services import task_service
from ..utils.decorators import api_login_required
from ..utils.responses import json_error, json_payload


def create_blueprint():
    bp = Blueprint("tasks", __name__)

    @bp.get("/api/tasks")
    @api_login_required
    def api_list_tasks():
        rows = task_service.list_tasks(
            session["user_id"],
            status=request.args.get("status"),
            priority=request.args.get("priority"),
            q=request.args.get("q", ""),
        )
        return json_payload({"tasks": rows})

    @bp.post("/api/tasks")
    @api_login_required
    def api_create_task():
        task, errors = task_service.create_task(
            session["user_id"], request.get_json(silent=True) or {}
        )
        if errors:
            return json_error(errors[0], errors=errors)
        return json_payload({"task": task}, status=201)

    @bp.put("/api/tasks/<int:task_id>")
    @api_login_required
    def api_update_task(task_id):
        task, errors = task_service.update_task(
            session["user_id"], task_id, request.get_json(silent=True) or {}
        )
        if errors:
            if "not found" in errors[0]:
                return json_error(errors[0], status=404)
            return json_error(errors[0], errors=errors)
        return json_payload({"task": task})

    @bp.delete("/api/tasks/<int:task_id>")
    @api_login_required
    def api_delete_task(task_id):
        if not task_service.delete_task(session["user_id"], task_id):
            return json_error("Task not found.", status=404)
        return json_payload({"ok": True}, status=204)

    return bp