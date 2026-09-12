"""Analytics endpoint — activity calendar + streak + weekly chart data."""

from flask import Blueprint, session

from ..services import analytics_service
from ..utils.decorators import api_login_required
from ..utils.responses import json_payload


def create_blueprint():
    bp = Blueprint("analytics", __name__)

    @bp.get("/api/analytics")
    @api_login_required
    def api_analytics():
        data = analytics_service.analytics(session["user_id"])
        return json_payload(data)

    return bp