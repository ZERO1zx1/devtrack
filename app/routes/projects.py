"""Project pages and REST API."""

from flask import Blueprint, render_template, request, session

from ..services import project_service
from ..utils.decorators import api_login_required, login_required
from ..utils.responses import json_error, json_payload


def create_blueprint():
    bp = Blueprint("projects", __name__)

    @bp.get("/projects")
    @login_required
    def projects_page():
        return render_template("projects/index.html")

    @bp.get("/api/projects")
    @api_login_required
    def api_list_projects():
        from ..models import project as project_model

        return json_payload({"projects": project_model.list_projects(session["user_id"])})

    @bp.post("/api/projects")
    @api_login_required
    def api_create_project():
        project, errors = project_service.create_project(
            session["user_id"], request.get_json(silent=True) or {}
        )
        if errors:
            return json_error(errors[0], errors=errors)
        return json_payload({"project": project}, status=201)

    @bp.put("/api/projects/<int:project_id>")
    @api_login_required
    def api_update_project(project_id):
        project, errors = project_service.update_project(
            session["user_id"], project_id, request.get_json(silent=True) or {}
        )
        if errors:
            if "not found" in errors[0]:
                return json_error(errors[0], status=404)
            return json_error(errors[0], errors=errors)
        return json_payload({"project": project})

    @bp.delete("/api/projects/<int:project_id>")
    @api_login_required
    def api_delete_project(project_id):
        if not project_service.delete_project(session["user_id"], project_id):
            return json_error("Project not found.", status=404)
        return json_payload({"ok": True}, status=204)

    return bp