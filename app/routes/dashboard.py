"""Dashboard routes."""

from flask import Blueprint, current_app, render_template, request

from app.services.pack_service import PackService
from app.utils.auth import login_required
from app.utils.guards import database_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
# @login_required  # Temporarily disabled for testing
@database_required
def index():
    user_id = current_app.config["DEFAULT_USER_ID"]
    service = PackService()
    stats = service.dashboard_stats(user_id)
    search = (request.args.get("q") or "").strip()
    search_results = []
    if search:
        search_results = service.list_packs(user_id=user_id, search=search, limit=20)

    return render_template(
        "dashboard/index.html",
        stats=stats,
        search=search,
        search_results=search_results,
    )
