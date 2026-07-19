"""Packs Flask application factory."""

import logging
import os
from flask import Flask

from config import config_by_name
from app.services.database import db


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_app(config_name: str = "default") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    config_cls = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_cls)
    
    # Log database configuration
    logger.info(f"Config: {config_name}")
    logger.info(f"Database configured: {app.config.get('DATABASE_CONFIGURED')}")
    logger.info(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', '').split('@')[0]}...")
    logger.info(f"SUPABASE_DB_URL env: {os.getenv('SUPABASE_DB_URL', 'NOT SET')[:50]}...")

    db.init_app(app)
    logger.info("Database initialized")

    _register_blueprints(app)
    _register_context_processors(app)

    return app


def _register_blueprints(app: Flask) -> None:
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.packs import packs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(packs_bp)


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        from flask import session

        return {
            "current_user": session.get("user"),
            "app_name": "Packs",
        }
