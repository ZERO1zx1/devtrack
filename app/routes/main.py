"""Public pages: landing page and the developer dashboard."""

from flask import Blueprint, render_template, session

from ..models import project as project_model
from ..services import analytics_service
from ..utils.decorators import login_required


def create_blueprint():
    bp = Blueprint("main", __name__)

    @bp.get("/")
    def index():
        return render_template("index.html")

    @bp.get("/dashboard")
    @login_required
    def dashboard():
        user_id = session["user_id"]
        return render_template(
            "tasks/dashboard.html",
            stats=analytics_service.analytics(user_id),
            projects=project_model.list_projects(user_id),
        )

    return bp