"""Route blueprints package."""

from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.packs import packs_bp

__all__ = ["auth_bp", "dashboard_bp", "packs_bp"]
